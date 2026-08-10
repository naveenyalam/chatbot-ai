from datetime import datetime
from pydantic import BaseModel, Field

class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default="nova-intelligence", max_length=100)

class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
