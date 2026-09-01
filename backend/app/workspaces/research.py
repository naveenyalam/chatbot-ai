from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.agents.manager import agent_manager


class ResearchWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.RESEARCH

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.RESEARCH.value,
            name="Research",
            description="Multi-source topic investigation, web search synthesis, and citation-backed reports",
            capabilities=["multi-step-search", "citation-accumulation", "structured-summarization", "comparative-analysis"],
            icon="search",
            supported_tools=["web_search", "document_search"],
            allowed_attachments=["text", "pdf"],
            suggested_prompts=[
                "Research the advantages and disadvantages of electric vehicles.",
                "Investigate recent breakthroughs in renewable energy technology.",
                "Summarize the competitive landscape of LLM providers in 2026."
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
