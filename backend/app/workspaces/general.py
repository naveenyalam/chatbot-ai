from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.agents.chat_agent import ChatAgent
from app.agents.manager import agent_manager


class GeneralWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.GENERAL

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.GENERAL.value,
            name="General AI",
            description="General multi-modal chat, reasoning, explanations, and Q&A assistant",
            capabilities=["multi-turn-chat", "reasoning", "explanations", "brainstorming", "general-knowledge"],
            icon="sparkles",
            supported_tools=["calculator"],
            allowed_attachments=["image", "text"],
            suggested_prompts=[
                "Explain quantum computing in simple terms",
                "How do I structure a modern web application?",
                "What are the key principles of clean architecture?"
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
