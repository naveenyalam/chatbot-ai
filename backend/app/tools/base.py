import abc
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Dict[str, Any]
    sources: List[Dict[str, Any]] = []
    error: Optional[str] = None

class Tool(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @abc.abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool action with the given input map.
        """
        pass
