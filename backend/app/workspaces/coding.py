from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import WorkspaceMetadata, WorkspaceChatRequest
from app.workspaces.base import BaseWorkspace
from app.agents.manager import agent_manager


class CodingWorkspace(BaseWorkspace):
    @property
    def mode(self) -> WorkspaceMode:
        return WorkspaceMode.CODING

    @property
    def metadata(self) -> WorkspaceMetadata:
        return WorkspaceMetadata(
            id=WorkspaceMode.CODING.value,
            name="Coding",
            description="Sandboxed programming, debugging, code generation, refactoring, and unit test generation",
            capabilities=["code-generation", "debugging", "algorithm-design", "code-explanation", "sandboxed-execution"],
            icon="code",
            supported_tools=["calculator", "code_execution"],
            allowed_attachments=["text", "python", "javascript", "typescript", "json"],
            suggested_prompts=[
                "Write a Python program to check whether a number is prime.",
                "Debug this code and explain why it throws a recursion error.",
                "Refactor this JavaScript function to use async/await."
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
