from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.agents.manager import agent_manager


class DocumentWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.DOCUMENTS

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.DOCUMENTS.value,
            name="Documents",
            description="RAG document retrieval and verified context analysis over indexed knowledge bases",
            capabilities=["document-search", "vector-retrieval", "context-citation", "chunking"],
            icon="file-text",
            supported_tools=["document_search"],
            allowed_attachments=["pdf", "docx", "txt", "md"],
            suggested_prompts=[
                "What are the key findings in the uploaded document?",
                "Summarize the terms of service from the attached PDF.",
                "Find the exact financial projections in the indexed documents."
            ]
        )

    def validate_request(self, req: WorkspaceChatRequest) -> List[str]:
        warnings = []
        if not req.document_ids or len(req.document_ids) == 0:
            warnings.append("No document_ids provided. RAG document retrieval will perform a global user library search.")
        return warnings

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
