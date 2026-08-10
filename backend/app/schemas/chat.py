from typing import Literal, List
from pydantic import BaseModel, Field, field_validator

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=60000, 
        description="The content text of the message"
    )

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        from app.core.config import settings
        if len(v) > settings.MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message content exceeds maximum allowed length of {settings.MAX_MESSAGE_LENGTH} characters.")
        return v

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str | None = Field(default=None, description="Model identifier to use")
    temperature: float = Field(
        default=0.7, 
        ge=0.0, 
        le=2.0, 
        description="Sampling temperature between 0.0 and 2.0"
    )
    conversation_id: str | None = Field(default=None, description="Optional conversation UUID")
    document_ids: List[str] | None = Field(default=None, description="Optional document UUIDs to restrict RAG search")
    mode: str | None = Field(default=None, description="Selected execution mode (normal, web_search, deep_research, document_search, multimodal)")
    workspace_mode: str | None = Field(default=None, description="Selected workspace mode (general, research, writing, coding, documents, data-analysis, agent)")


    @field_validator("messages")
    @classmethod
    def validate_messages_non_empty(cls, v: List[ChatMessage]) -> List[ChatMessage]:
        if not v:
            raise ValueError("Messages list cannot be empty")
        if len(v) > 200:
            raise ValueError("Conversation list exceeds system context limits (maximum 200 messages)")
        return v
