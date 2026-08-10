import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36), 
        ForeignKey("conversations.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    role = Column(String(50), nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="complete")  # sending, streaming, complete, error
    # Index on created_at for chronological sorting
    created_at = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(), 
        index=True
    )
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    sources = relationship("MessageSource", back_populates="message", cascade="all, delete-orphan", passive_deletes=True)


class MessageSource(Base):
    __tablename__ = "message_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(512), nullable=False)
    url = Column(String(2048), nullable=False)
    domain = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )

    message = relationship("Message", back_populates="sources")

