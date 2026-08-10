import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class AgentRun(Base):
    """
    Operational record of a single agent execution.
    Stores metadata only — no chain-of-thought, no sensitive content.
    """
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    mode = Column(String(50), nullable=False, default="normal")
    status = Column(String(50), nullable=False, default="running")  # running, complete, failed, cancelled, timeout
    step_count = Column(Integer, nullable=False, default=0)
    tool_call_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    tool_calls = relationship("AgentToolCall", back_populates="agent_run", cascade="all, delete-orphan")


class AgentToolCall(Base):
    """
    Operational record of a single tool call within an agent run.
    """
    __tablename__ = "agent_tool_calls"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="running")  # running, success, failed, retried
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    agent_run = relationship("AgentRun", back_populates="tool_calls")
