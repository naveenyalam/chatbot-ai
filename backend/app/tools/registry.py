from typing import Dict, Optional
from app.tools.base import Tool
from app.tools.search import WebSearchTool
from app.tools.calculator import CalculatorTool
from app.tools.code_execution import CodeExecutionTool
from app.tools.document_search import DocumentSearchTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        # Register standard default tools
        self.register(WebSearchTool())
        self.register(CalculatorTool())
        self.register(CodeExecutionTool())
        self.register(DocumentSearchTool())

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

# Global tool registry singleton
tool_registry = ToolRegistry()
