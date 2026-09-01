from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from app.workspaces.enums import WorkspaceMode

class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str]
    icon: str
    supported_tools: List[str] = Field(default_factory=list)
    allowed_attachments: List[str] = Field(default_factory=list)
    suggested_prompts: List[str] = Field(default_factory=list)

class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceMetadata]

class WorkspaceChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_content_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v

class WorkspaceChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: Optional[str] = None
    messages: Optional[List[WorkspaceChatMessage]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    document_ids: Optional[List[str]] = None
    response_style: Optional[str] = None
    response_tone: Optional[str] = None
    semantic_chunk_limit: Optional[int] = None
    similarity_filtering: Optional[bool] = None

    @field_validator("message")
    @classmethod
    def validate_single_or_messages(cls, v: Optional[str], info) -> Optional[str]:
        return v

class WorkspaceValidationResult(BaseModel):
    valid: bool
    workspace_mode: str
    warnings: List[str] = Field(default_factory=list)
