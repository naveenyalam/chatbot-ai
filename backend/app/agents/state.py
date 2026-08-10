"""
Agent State — explicit, observable, and bounded state container for every agent execution.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ToolActivityItem:
    """A single observable tool action record."""
    tool: str
    label: str
    status: str = "pending"        # pending | running | success | failed
    duration: Optional[float] = None
    result_preview: Optional[str] = None


@dataclass
class AgentState:
    """
    Holds all runtime state for a single agent execution.
    Never shared across requests.
    """
    request_id: str
    user_id: str
    conversation_id: Optional[str]
    mode: str

    # Progress counters
    step: int = 0
    tool_calls: int = 0

    # Lifecycle
    status: str = "running"          # running | complete | failed | cancelled | timeout
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Context accumulation
    messages: List[Dict[str, str]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    tool_activity: List[ToolActivityItem] = field(default_factory=list)

    # Database record ID (populated after AgentRun row is created)
    db_run_id: Optional[str] = None

    # Cancellation flag (set to True by stop button)
    cancelled: bool = False

    def add_tool_activity(self, tool: str, label: str) -> ToolActivityItem:
        item = ToolActivityItem(tool=tool, label=label, status="running")
        self.tool_activity.append(item)
        return item

    def mark_tool_complete(self, item: ToolActivityItem, duration: float, preview: str = ""):
        item.status = "success"
        item.duration = round(duration, 3)
        item.result_preview = preview[:200] if preview else ""

    def mark_tool_failed(self, item: ToolActivityItem, duration: float):
        item.status = "failed"
        item.duration = round(duration, 3)

    def to_activity_dict(self) -> list:
        return [
            {
                "tool": a.tool,
                "label": a.label,
                "status": a.status,
                "duration": a.duration,
                "result_preview": a.result_preview
            }
            for a in self.tool_activity
        ]
