"""
Base Agent — abstract foundation for all NOVA AI agent implementations.
"""
import abc
import logging
import time
from typing import AsyncGenerator, Dict, Any, List

from app.agents.state import AgentState, ToolActivityItem
from app.agents.policies import AgentPolicy
from app.agents.planner import AgentPlanner, PlanStep
from app.tools.registry import tool_registry
from app.core.errors import ToolExecutionError
from app.core.config import settings

logger = logging.getLogger("nova-ai.agents.base")


class BaseAgent(abc.ABC):
    """Abstract base class for all NOVA AI agents."""

    def __init__(self):
        self.planner = AgentPlanner()

    @property
    @abc.abstractmethod
    def agent_type(self) -> str:
        pass

    @abc.abstractmethod
    def get_allowed_tools(self) -> set[str]:
        pass

    @abc.abstractmethod
    async def run(
        self,
        state: AgentState,
        db=None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    async def _execute_tool_with_retry(
        self,
        state: AgentState,
        plan_step: PlanStep
    ) -> Dict[str, Any]:
        """Execute a tool with retry logic for transient failures."""
        import asyncio
        tool_name = plan_step.tool_name
        tool_input = plan_step.tool_input or {}
        max_retries = settings.TOOL_MAX_RETRIES

        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise ToolExecutionError(tool_name, f"Tool '{tool_name}' not found in registry.")

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                start = time.time()
                # Wrap with per-tool timeout
                result = await asyncio.wait_for(
                    tool.execute(tool_input),
                    timeout=float(settings.TOOL_TIMEOUT_SECONDS)
                )
                elapsed = time.time() - start

                data = result.data
                # Truncate output size if it exceeds bounds
                if len(str(data)) > settings.MAX_TOOL_OUTPUT_CHARS:
                    logger.warning(
                        f"Tool '{tool_name}' returned payload of size {len(str(data))}, "
                        f"truncating to {settings.MAX_TOOL_OUTPUT_CHARS}"
                    )
                    if isinstance(data, dict):
                        for key in ["stdout", "content", "snippet", "results"]:
                            if key in data:
                                if isinstance(data[key], str) and len(data[key]) > settings.MAX_TOOL_OUTPUT_CHARS:
                                    data[key] = data[key][:settings.MAX_TOOL_OUTPUT_CHARS] + "\n... [TRUNCATED] ..."
                                elif isinstance(data[key], list):
                                    data[key] = data[key][:5]  # limit list size
                        if len(str(data)) > settings.MAX_TOOL_OUTPUT_CHARS:
                            data = {"warning": f"Output truncated. Exceeded limit of {settings.MAX_TOOL_OUTPUT_CHARS} characters."}
                    elif isinstance(data, str):
                        data = data[:settings.MAX_TOOL_OUTPUT_CHARS] + "\n... [TRUNCATED] ..."
                    else:
                        data = str(data)[:settings.MAX_TOOL_OUTPUT_CHARS] + "\n... [TRUNCATED] ..."

                return {
                    "tool": tool_name,
                    "success": result.success,
                    "data": data,
                    "sources": result.sources,
                    "error": result.error,
                    "elapsed": round(elapsed, 3)
                }
            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning(f"Tool '{tool_name}' attempt {attempt+1} timed out after {settings.TOOL_TIMEOUT_SECONDS}s.")
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    logger.warning(
                        f"Tool '{tool_name}' attempt {attempt+1} failed: {exc}. Retrying..."
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))  # exponential backoff
                else:
                    logger.error(f"Tool '{tool_name}' failed after {max_retries+1} attempts: {exc}")

        raise ToolExecutionError(tool_name, str(last_error))

    def _build_tool_context_message(self, tool_results: list) -> str:
        """Format tool results into a context message for the LLM."""
        import json
        parts = []
        for tr in tool_results:
            tool = tr.get("tool", "unknown")
            data = tr.get("data", {})
            sources = tr.get("sources", [])

            if tool == "web_search" and data.get("results"):
                for r in data["results"][:5]:
                    parts.append(
                        f"[{tool}] {r.get('title', '')}: {r.get('snippet', '')[:300]}"
                    )
            elif tool == "calculator":
                expr = data.get("expression", "")
                result = data.get("result", "")
                parts.append(f"[calculator] {expr} = {result}")
            elif tool == "code_execution":
                stdout = data.get("stdout", "")
                stderr = data.get("stderr", "")
                exit_code = data.get("exit_code", 0)
                parts.append(
                    f"[code_execution] exit_code={exit_code}\n"
                    f"stdout: {stdout[:500]}\n"
                    f"stderr: {stderr[:200]}"
                )
            elif tool == "document_search":
                results = data.get("results", [])
                for r in results[:3]:
                    parts.append(f"[document] {r.get('content', '')[:400]}")
            else:
                parts.append(f"[{tool}] {json.dumps(data, default=str)[:400]}")

        return "\n\n".join(parts)
