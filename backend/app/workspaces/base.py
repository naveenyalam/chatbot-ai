import abc
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest

logger = logging.getLogger("nova-ai.workspaces.base")


class BaseWorkspace(abc.ABC):
    """
    Abstract Base Class for NOVA AI Workspace Modes.
    """

    @property
    @abc.abstractmethod
    def mode(self) -> WorkspaceMode:
        """The canonical WorkspaceMode enum value."""
        pass

    @property
    @abc.abstractmethod
    def metadata(self) -> WorkspaceMetadata:
        """Workspace metadata including name, capabilities, icon, tools, and suggested prompts."""
        pass

    def validate_request(self, req: WorkspaceChatRequest) -> List[str]:
        """
        Perform mode-specific request validation.
        Returns a list of warning strings or raises ValueError for fatal validation errors.
        """
        return []

    @abc.abstractmethod
    async def execute_stream(
        self,
        request_id: str,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, str]],
        req: WorkspaceChatRequest,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the workspace AI pipeline and yield structured SSE event objects.
        """
        pass
