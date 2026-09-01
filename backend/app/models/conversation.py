import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    title = Column(String(200), nullable=False)
    model = Column(String(100), nullable=False, default="nova-intelligence")
    workspace_mode = Column(String(50), nullable=False, default="general")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    # Index on updated_at for descending list sorting
    updated_at = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now(), 
        index=True
    )

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", 
        back_populates="conversation", 
        cascade="all, delete-orphan",
        passive_deletes=True
    )
