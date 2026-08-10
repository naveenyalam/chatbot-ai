"""
Safe Calculator Tool using Python's AST module.

Supports: +, -, *, /, //, %, **, (), unary minus, abs, round, min, max, sum, int, float
Rejects: imports, function definitions, attribute access, exec/eval, any non-whitelisted name
"""
import ast
import logging
import math
from typing import Any, Dict

from app.tools.base import Tool, ToolResult
from app.core.errors import CalculatorError

logger = logging.getLogger("nova-ai.tools.calculator")

# Whitelisted safe names
_SAFE_NAMES = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "int": int,
    "float": float,
    "pow": pow,
    "True": True,
    "False": False,
}

# Whitelisted AST node types
_SAFE_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,       # Python < 3.8
    ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow,
    ast.USub, ast.UAdd,
    ast.Call,
    ast.Name,
    ast.List, ast.Tuple,
    ast.Load,
)


def _validate_ast(node: ast.AST) -> None:
    """Recursively walk AST and raise CalculatorError for any unsafe node."""
    if not isinstance(node, _SAFE_NODES):
        raise CalculatorError(f"Forbidden operation: {type(node).__name__}")

    # Check function calls are only whitelisted names
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Attribute access and method calls are not allowed.")
        if node.func.id not in _SAFE_NAMES:
            raise CalculatorError(f"Function '{node.func.id}' is not allowed.")

    # Check Name references are only whitelisted constants
    if isinstance(node, ast.Name):
        if node.id not in _SAFE_NAMES:
            raise CalculatorError(f"Name '{node.id}' is not allowed.")

    for child in ast.iter_child_nodes(node):
        _validate_ast(child)


class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions safely. Supports +, -, *, /, %, **, (), abs, round, min, max."

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        expression = input_data.get("expression", "").strip()

        if not expression:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error="No expression provided."
            )

        if len(expression) > 1000:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={},
                error="Expression too long (max 1000 characters)."
            )

        try:
            tree = ast.parse(expression, mode="eval")
            _validate_ast(tree.body)

            # Safe eval with only whitelisted builtins
            result = eval(
                compile(tree, filename="<expr>", mode="eval"),
                {"__builtins__": {}},
                _SAFE_NAMES
            )

            # Guard against extremely large numbers
            result_str = str(result)
            if len(result_str) > 200:
                result_str = result_str[:200] + "..."

            logger.info(f"Calculator evaluated: '{expression}' = {result_str}")
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"expression": expression, "result": result_str}
            )

        except CalculatorError as ce:
            logger.warning(f"Calculator rejected expression '{expression}': {ce}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"expression": expression},
                error=str(ce)
            )
        except ZeroDivisionError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"expression": expression},
                error="Division by zero."
            )
        except Exception as e:
            logger.error(f"Calculator unexpected error for '{expression}': {e}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                data={"expression": expression},
                error=f"Could not evaluate expression: {e}"
            )
