"""
Sandboxed Code Execution Tool with Sandbox Provider abstraction.

Provides:
- BaseSandbox interface
- RestrictedPythonSandbox: AST-restricted in-process sandbox
- DockerSandbox: Ephemeral docker-container based sandbox (preferred in production)
"""
import asyncio
import io
import logging
import os
import sys
import tempfile
import time
from typing import Any, Dict

from pydantic import BaseModel
from RestrictedPython import compile_restricted, safe_globals, safe_builtins
from RestrictedPython.Guards import (
    safer_getattr,
    guarded_setattr,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
)

from app.tools.base import Tool, ToolResult
from app.core.config import settings
from app.core.errors import SandboxError

logger = logging.getLogger("nova-ai.tools.code-execution")

SUPPORTED_LANGUAGES = {"python"}


class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int | None = None
    execution_time: float = 0.0
    language: str = "python"


class BaseSandbox:
    """Base class defining the execution interface for all code sandboxes."""
    async def execute(self, code: str, timeout: float, memory_mb: int) -> ExecutionResult:
        raise NotImplementedError()


def _build_restricted_globals(stdout_io: io.StringIO) -> dict:
    """Build a fully isolated global namespace for RestrictedPython execution."""
    from RestrictedPython import safe_globals, safe_builtins

    # Start with RestrictedPython safe globals
    restricted = dict(safe_globals)

    # Build safe builtins — allow only essential non-IO functions
    safe_builtins_copy = dict(safe_builtins)

    # Remove dangerous builtins
    for blocked in ["open", "compile", "exec", "eval", "__import__", "input",
                    "breakpoint", "memoryview", "staticmethod", "classmethod",
                    "super", "vars", "dir", "globals", "locals", "delattr", "setattr"]:
        safe_builtins_copy.pop(blocked, None)

    safe_builtins_copy.update({
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "reversed": reversed,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "bytes": bytes,
        "len": len,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "any": any,
        "all": all,
        "isinstance": isinstance,
        "type": type,
    })

    restricted["__builtins__"] = safe_builtins_copy

    # RestrictedPython uses _print_ for print()
    class _PrintCollector:
        """Collects print output into the stdout_io buffer."""
        def __init__(self, _getattr=None):
            self._getattr = _getattr

        def _call_print(self, *objects, **kwargs):
            line = " ".join(str(o) for o in objects) + "\n"
            stdout_io.write(line)

        def write(self, s):
            stdout_io.write(s)

        def __str__(self):
            return ""

    restricted["_print_"] = _PrintCollector

    def strict_getattr(obj, name, default=None):
        if isinstance(name, str) and name.startswith("_"):
            raise AttributeError(f"Access to private or dunder attribute '{name}' is blocked.")
        return safer_getattr(obj, name, default)

    def strict_inplacevar(op, x, y):
        import operator
        ops = {
            "+=": operator.iadd,
            "-=": operator.isub,
            "*=": operator.imul,
            "/=": operator.itruediv,
            "//=": operator.ifloordiv,
            "%=": operator.imod,
            "**=": operator.ipow,
            "<<=": operator.ilshift,
            ">>=": operator.irshift,
            "&=": operator.iand,
            "|=": operator.ior,
            "^=": operator.ixor,
        }
        if op in ops:
            return ops[op](x, y)
        raise NotImplementedError(f"Operator {op} is not supported in sandboxed inplace operations.")

    # Guard functions required by RestrictedPython
    restricted["_getattr_"] = strict_getattr
    restricted["_getitem_"] = lambda obj, key: obj[key]
    restricted["_setattr_"] = guarded_setattr
    restricted["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
    restricted["_unpack_sequence_"] = guarded_unpack_sequence
    restricted["_getiter_"] = iter
    restricted["_write_"] = lambda x: x
    restricted["_inplacevar_"] = strict_inplacevar

    return restricted


def _run_in_sandbox(code: str, workspace_dir: str) -> ExecutionResult:
    """
    Compile and execute Python code inside a RestrictedPython sandbox.
    This is called from a thread pool to allow asyncio timeout.
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        byte_code = compile_restricted(code, filename="<sandbox>", mode="exec")
    except SyntaxError as se:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"SyntaxError: {se}",
            exit_code=1,
            execution_time=0.0
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Compilation error: {e}",
            exit_code=1,
            execution_time=0.0
        )

    restricted_globals = _build_restricted_globals(stdout_capture)
    restricted_globals["__workspace__"] = workspace_dir

    start_time = time.time()
    exit_code = 0

    try:
        exec(byte_code, restricted_globals, {})
    except Exception as e:
        stderr_capture.write(f"{type(e).__name__}: {e}\n")
        exit_code = 1

    elapsed = time.time() - start_time

    stdout_val = stdout_capture.getvalue()
    stderr_val = stderr_capture.getvalue()

    # Truncate output
    max_out = settings.CODE_EXECUTION_MAX_OUTPUT
    if len(stdout_val) > max_out:
        stdout_val = stdout_val[:max_out] + f"\n[Output truncated at {max_out} characters]"
    if len(stderr_val) > max_out:
        stderr_val = stderr_val[:max_out] + "\n[Stderr truncated]"

    return ExecutionResult(
        success=exit_code == 0,
        stdout=stdout_val,
        stderr=stderr_val,
        exit_code=exit_code,
        execution_time=round(elapsed, 3)
    )


class RestrictedPythonSandbox(BaseSandbox):
    """In-process RestrictedPython based security sandbox."""
    async def execute(self, code: str, timeout: float, memory_mb: int) -> ExecutionResult:
        workspace_dir = tempfile.mkdtemp(prefix="nova_sandbox_")
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_in_sandbox, code, workspace_dir)
            return result
        finally:
            import shutil
            shutil.rmtree(workspace_dir, ignore_errors=True)


class DockerSandbox(BaseSandbox):
    """Containerized sandbox running inside an ephemeral Docker container."""
    async def execute(self, code: str, timeout: float, memory_mb: int) -> ExecutionResult:
        # Run using a minimal python-alpine container with CPU limits, memory limits, and network access disabled
        cmd = [
            "docker", "run", "--rm", "-i",
            "-m", f"{memory_mb}m",
            "--cpus", "0.5",
            "--network", "none",
            "python:3.10-alpine", "python", "-"
        ]
        
        logger.info(f"Launching Docker sandbox container: {' '.join(cmd)}")
        start_time = time.time()
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except Exception as exc:
            logger.warning(f"Docker sandbox process creation failed: {exc}")
            raise RuntimeError(f"Docker daemon or command not available: {exc}")

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=code.encode("utf-8")),
                timeout=timeout
            )
            elapsed = time.time() - start_time
            exit_code = proc.returncode
            
            stdout_val = stdout_bytes.decode("utf-8", errors="replace")
            stderr_val = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate output
            max_out = settings.CODE_EXECUTION_MAX_OUTPUT
            if len(stdout_val) > max_out:
                stdout_val = stdout_val[:max_out] + f"\n[Output truncated at {max_out} characters]"
            if len(stderr_val) > max_out:
                stderr_val = stderr_val[:max_out] + "\n[Stderr truncated]"

            return ExecutionResult(
                success=exit_code == 0,
                stdout=stdout_val,
                stderr=stderr_val,
                exit_code=exit_code,
                execution_time=round(elapsed, 3)
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            logger.warning(f"Docker sandbox execution timed out after {timeout} seconds.")
            raise asyncio.TimeoutError()


class CodeExecutionTool(Tool):
    @property
    def name(self) -> str:
        return "code_execution"

    @property
    def description(self) -> str:
        return "Execute Python code in a sandboxed environment and return the output."

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        language = input_data.get("language", "python").lower()
        code = input_data.get("code", "").strip()

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"language": language},
                error=f"Language '{language}' is not supported. Supported: {', '.join(SUPPORTED_LANGUAGES)}."
            )

        # Validate code size
        if not code:
            return ToolResult(tool_name=self.name, success=False, data={}, error="No code provided.")

        if len(code) > settings.CODE_EXECUTION_MAX_CODE_SIZE:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error=f"Code exceeds maximum size of {settings.CODE_EXECUTION_MAX_CODE_SIZE} characters."
            )

        timeout = float(settings.CODE_EXECUTION_TIMEOUT)
        memory = settings.CODE_EXECUTION_MEMORY_MB

        # Select sandbox provider
        # Try DockerSandbox first. If it fails due to environment limitations, fall back to RestrictedPythonSandbox.
        sandbox = DockerSandbox()
        using_fallback = False
        
        try:
            result = await sandbox.execute(code, timeout, memory)
        except (RuntimeError, asyncio.TimeoutError, Exception) as exc:
            if isinstance(exc, asyncio.TimeoutError):
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={"language": language, "code": code[:200]},
                    error=f"Code execution timed out after {timeout} seconds."
                )
                
            # If Docker daemon is unavailable, fallback to RestrictedPythonSandbox
            logger.warning(f"DockerSandbox failed ({exc}). Falling back to RestrictedPythonSandbox.")
            using_fallback = True
            sandbox = RestrictedPythonSandbox()
            
            try:
                result = await asyncio.wait_for(
                    sandbox.execute(code, timeout, memory),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={"language": language, "code": code[:200]},
                    error=f"Code execution timed out after {timeout} seconds."
                )
            except Exception as fallback_exc:
                logger.exception(f"Fallback sandbox failed: {fallback_exc}")
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data={"language": language},
                    error=f"Sandbox execution failed: {fallback_exc}"
                )

        logger.info(
            f"Code executed: success={result.success}, "
            f"fallback={using_fallback}, exit_code={result.exit_code}, time={result.execution_time}s"
        )

        return ToolResult(
            tool_name=self.name,
            success=result.success,
            data={
                "language": language,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time": result.execution_time,
                "sandbox_fallback": using_fallback
            }
        )
