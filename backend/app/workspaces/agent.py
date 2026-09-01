from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.agents.manager import agent_manager


class AgentWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.AGENT

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.AGENT.value,
            name="Agent Workspace",
            description="Autonomous multi-step task execution, tool orchestration, planning, and sandboxed calculations",
            capabilities=["multi-step-planning", "tool-execution", "calculator", "code-sandbox", "web-search"],
            icon="bot",
            supported_tools=["calculator", "web_search", "document_search", "code_execution"],
            allowed_attachments=["text", "pdf", "json", "code"],
            suggested_prompts=[
                "Calculate total project cost and research market rates for comparison.",
                "Search for recent AI news, filter top 3 articles, and write a summary.",
                "Run Python code to process data and generate a structured report."
            ]
        )

    async def execute_stream(
        self,
        request_id: str,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, str]],
        req: WorkspaceChatRequest,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        async for event in agent_manager.execute(
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages,
            mode=self.mode.value,
            document_ids=req.document_ids or [],
            model_alias=req.model,
            temperature=req.temperature,
            db=db,
            response_style=req.response_style,
            response_tone=req.response_tone,
            semantic_chunk_limit=req.semantic_chunk_limit,
            similarity_filtering=req.similarity_filtering
        ):
            yield event
