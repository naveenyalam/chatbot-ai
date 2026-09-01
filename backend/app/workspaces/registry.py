import logging
from typing import Dict, List, Optional
from fastapi import HTTPException, status

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata
from app.workspaces.base import BaseWorkspace
from app.workspaces.general import GeneralWorkspace
from app.workspaces.research import ResearchWorkspace
from app.workspaces.writing import WritingWorkspace
from app.workspaces.coding import CodingWorkspace
from app.workspaces.documents import DocumentWorkspace
from app.workspaces.data_analysis import DataAnalysisWorkspace
from app.workspaces.agent import AgentWorkspace

logger = logging.getLogger("nova-ai.workspaces.registry")


class WorkspaceRegistry:
    """
    Central Registry for all NOVA AI Workspace Modes.
    """

    def __init__(self):
        self._workspaces: Dict[WorkspaceMode, BaseWorkspace] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(GeneralWorkspace())
        self.register(ResearchWorkspace())
        self.register(WritingWorkspace())
        self.register(CodingWorkspace())
        self.register(DocumentWorkspace())
        self.register(DataAnalysisWorkspace())
        self.register(AgentWorkspace())

    def register(self, workspace: BaseWorkspace):
        """Register a workspace implementation."""
        if not isinstance(workspace, BaseWorkspace):
            raise TypeError("Workspace must inherit from BaseWorkspace")
        self._workspaces[workspace.mode] = workspace
        logger.info(f"Registered workspace mode: {workspace.mode.value}")

    def is_supported(self, mode_raw: Optional[str]) -> bool:
        """Check whether the given mode string maps to a registered workspace mode."""
        if not mode_raw:
            return False
        normalized = WorkspaceMode.normalize(mode_raw)
        return normalized is not None and normalized in self._workspaces

    def get_workspace(self, mode_raw: Optional[str]) -> BaseWorkspace:
        """
        Get the workspace instance for a mode string or WorkspaceMode enum.
        Raises HTTP 404/422 if invalid/unknown mode.
        """
        if not mode_raw:
            return self._workspaces[WorkspaceMode.GENERAL]

        normalized = WorkspaceMode.normalize(mode_raw)
        if normalized is None or normalized not in self._workspaces:
            logger.warning(f"Unknown workspace requested: '{mode_raw}'")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "UNKNOWN_WORKSPACE_MODE",
                    "message": f"Workspace '{mode_raw}' not found.",
                    "valid_modes": [m.value for m in WorkspaceMode]
                }
            )
        return self._workspaces[normalized]

    def list_workspaces(self) -> List[WorkspaceMetadata]:
        """List metadata for all registered workspace modes."""
        return [ws.metadata for ws in self._workspaces.values()]


# Global singleton
workspace_registry = WorkspaceRegistry()
