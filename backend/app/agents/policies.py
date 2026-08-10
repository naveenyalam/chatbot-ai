"""
Agent Policy Layer — enforces tool permissions and execution limits.

Each agent type has an explicit allowlist of tools it may use.
The policy layer is the single source of truth for authorization.
"""
from typing import Set
from app.core.config import settings
from app.core.errors import AgentTimeoutError, AgentStepLimitError
from app.agents.state import AgentState
import logging
import time

logger = logging.getLogger("nova-ai.agents.policy")

# Per-agent tool allowlists — agents CANNOT use tools not in their list
AGENT_TOOL_POLICIES: dict[str, Set[str]] = {
    "normal":   {"calculator"},
    "chat":     {"calculator"},
    "research": {"web_search", "document_search"},
    "document": {"document_search"},
    "task":     {"calculator", "web_search", "document_search", "code_execution"},
    "agent":    {"calculator", "web_search", "document_search", "code_execution"},
}


class AgentPolicy:
    """
    Validates tool permissions and operational limits for agent execution.
    All agent code MUST call these checks before every tool invocation.
    """

    @staticmethod
    def allowed_tools(mode: str) -> Set[str]:
        return AGENT_TOOL_POLICIES.get(mode, set())

    @staticmethod
    def can_use_tool(mode: str, tool_name: str) -> bool:
        allowed = AGENT_TOOL_POLICIES.get(mode, set())
        result = tool_name in allowed
        if not result:
            logger.warning(
                f"Policy denied: agent mode='{mode}' attempted to use tool='{tool_name}'. "
                f"Allowed: {allowed}"
            )
        return result

    @staticmethod
    def check_step_limit(state: AgentState) -> None:
        """Raise if agent has exceeded max step count."""
        limit = settings.MAX_AGENT_STEPS
        if state.step >= limit:
            try:
                from app.core.metrics import AGENT_LIMIT_EXCEEDED_TOTAL
                AGENT_LIMIT_EXCEEDED_TOTAL.labels(agent_type=state.mode).inc()
            except Exception:
                pass
            raise AgentStepLimitError(limit)

    @staticmethod
    def check_tool_call_limit(state: AgentState) -> None:
        """Raise if agent has exceeded max tool call count."""
        limit = settings.AGENT_MAX_TOOL_CALLS
        if state.tool_calls >= limit:
            try:
                from app.core.metrics import AGENT_LIMIT_EXCEEDED_TOTAL
                AGENT_LIMIT_EXCEEDED_TOTAL.labels(agent_type=state.mode).inc()
            except Exception:
                pass
            raise AgentStepLimitError(limit)

    @staticmethod
    def check_timeout(state: AgentState) -> None:
        """Raise if agent has exceeded wall-clock timeout."""
        from datetime import datetime
        elapsed = (datetime.utcnow() - state.started_at).total_seconds()
        limit = settings.AGENT_TIMEOUT_SECONDS
        if elapsed > limit:
            try:
                from app.core.metrics import AGENT_TIMEOUT_TOTAL
                AGENT_TIMEOUT_TOTAL.labels(agent_type=state.mode).inc()
            except Exception:
                pass
            raise AgentTimeoutError(limit)

    @staticmethod
    def check_all_limits(state: AgentState) -> None:
        """Run all limit checks in one call."""
        AgentPolicy.check_timeout(state)
        AgentPolicy.check_step_limit(state)
        if state.cancelled:
            try:
                from app.core.metrics import AGENT_CANCELLED_TOTAL
                AGENT_CANCELLED_TOTAL.labels(agent_type=state.mode).inc()
            except Exception:
                pass
            from app.core.errors import NOVABaseError
            raise NOVABaseError(
                "Agent cancelled by user",
                user_message="Agent execution was stopped."
            )
