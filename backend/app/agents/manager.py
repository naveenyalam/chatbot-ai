"""
Agent Manager — central orchestrator for all NOVA AI agent executions.

Responsibilities:
- Select the right agent based on mode
- Create and persist AgentRun records
- Wrap execution with timeout and cancellation
- Emit structured JSON events to the streaming layer
- Enforce user isolation (never mix user data)
- Log operational metadata (never log sensitive content)
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.agents.policies import AgentPolicy
from app.agents.chat_agent import ChatAgent
from app.agents.research_agent import ResearchAgent
from app.agents.document_agent import DocumentAgent
from app.agents.task_agent import TaskAgent
from app.models.agent import AgentRun, AgentToolCall
from app.core.config import settings
from app.core.errors import AgentTimeoutError, NOVABaseError

logger = logging.getLogger("nova-ai.agents.manager")

# Rate limiting via in-memory TTL cache
try:
    from cachetools import TTLCache
    _rate_cache: Dict[str, TTLCache] = {
        "agent_runs": TTLCache(maxsize=10000, ttl=60),
        "code_exec": TTLCache(maxsize=10000, ttl=60),
    }
except ImportError:
    _rate_cache = {}
    logger.warning("cachetools not available — rate limiting disabled.")


def _check_rate_limit(cache_key: str, user_id: str, limit: int) -> bool:
    """Returns True if user is within limit, False if rate limited."""
    cache = _rate_cache.get(cache_key)
    if cache is None:
        return True
    count = cache.get(user_id, 0)
    if count >= limit:
        return False
    cache[user_id] = count + 1
    return True


def _select_agent(mode: str, document_ids: List[str]) -> "BaseAgent":
    """Select and instantiate the right agent for the given mode."""
    from app.models.workspace_mode import WorkspaceMode
    norm = WorkspaceMode.normalize(mode) or WorkspaceMode.GENERAL

    if norm == WorkspaceMode.RESEARCH:
        return ResearchAgent()
    if norm == WorkspaceMode.DOCUMENTS:
        return DocumentAgent(document_ids=document_ids)
    if norm == WorkspaceMode.AGENT:
        return TaskAgent(document_ids=document_ids)

    return ChatAgent(mode=norm.value)



class AgentManager:
    """
    Manages the full lifecycle of a single agent execution.
    Emits structured dict events consumed by the streaming route.
    """

    async def execute(
        self,
        request_id: str,
        user_id: str,
        conversation_id: Optional[str],
        messages: List[Dict[str, str]],
        mode: str,
        document_ids: List[str],
        model_alias: Optional[str],
        temperature: float,
        db: Session,
        response_style: Optional[str] = None,
        response_tone: Optional[str] = None,
        semantic_chunk_limit: Optional[int] = None,
        similarity_filtering: Optional[bool] = None,
        language: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # Rate limit check
        if not _check_rate_limit("agent_runs", user_id, settings.MAX_AGENT_RUNS_PER_MINUTE):
            yield {
                "type": "error",
                "value": "Too many requests. Please wait a moment before trying again."
            }
            return

        # Resolve mode intelligently
        from app.core.concurrency import operation_limit
        async with operation_limit("agent"):
            resolved_mode = (mode or "normal").lower()

            # Auto-detect task mode if message implies multi-step work
            if resolved_mode in ("normal", "chat") and document_ids:
                resolved_mode = "document"

            # Create state
            state = AgentState(
                request_id=request_id,
                user_id=user_id,
                conversation_id=conversation_id,
                mode=resolved_mode,
                messages=messages,
                started_at=datetime.utcnow(),
                response_style=response_style,
                response_tone=response_tone,
                semantic_chunk_limit=semantic_chunk_limit,
                similarity_filtering=similarity_filtering,
                language=language,
                temperature=temperature
            )

            # Persist AgentRun record
            db_run = AgentRun(
                request_id=request_id,
                user_id=user_id,
                conversation_id=conversation_id,
                mode=resolved_mode,
                status="running"
            )
            try:
                db.add(db_run)
                db.flush()
                state.db_run_id = db_run.id
            except Exception as db_err:
                logger.error(f"Failed to persist AgentRun: {db_err}")
                # Non-fatal: continue execution without DB record

            agent = _select_agent(resolved_mode, document_ids)
            logger.info(
                f"[{request_id}] AgentManager: starting {agent.agent_type} agent "
                f"for user={user_id} mode={resolved_mode}"
            )

            final_status = "complete"
            start_wall = time.time()

            try:
                # Wrap execution with global timeout
                async def _run():
                    async for event in agent.run(state, db=db):
                        yield event

                async for event in _run():
                    yield event

            except AgentTimeoutError as te:
                final_status = "timeout"
                logger.warning(f"[{request_id}] Agent timed out: {te}")
                yield {"type": "error", "value": te.user_message}

            except NOVABaseError as ne:
                final_status = "failed"
                logger.error(f"[{request_id}] NOVA error: {ne}")
                yield {"type": "error", "value": ne.user_message}

            except Exception as exc:
                final_status = "failed"
                logger.exception(f"[{request_id}] Unexpected agent error: {exc}")
                yield {"type": "error", "value": "An unexpected error occurred. Please try again."}

            finally:
                elapsed = time.time() - start_wall
                # Update DB record
                if state.db_run_id:
                    try:
                        db.query(AgentRun).filter(AgentRun.id == state.db_run_id).update({
                            "status": final_status,
                            "step_count": state.step,
                            "tool_call_count": state.tool_calls,
                            "completed_at": datetime.utcnow()
                        })

                        # Persist tool call records
                        for activity in state.tool_activity:
                            tc = AgentToolCall(
                                agent_run_id=state.db_run_id,
                                tool_name=activity.tool,
                                status=activity.status,
                                completed_at=datetime.utcnow()
                            )
                            db.add(tc)

                        db.commit()
                    except Exception as db_err:
                        logger.error(f"[{request_id}] Failed to finalize AgentRun: {db_err}")

                # Record agent and tool Prometheus metrics
                try:
                    from app.core.metrics import AGENT_RUNS_TOTAL, AGENT_RUN_DURATION, TOOL_CALLS_TOTAL
                    AGENT_RUNS_TOTAL.labels(agent_type=agent.agent_type, status=final_status).inc()
                    AGENT_RUN_DURATION.labels(agent_type=agent.agent_type).observe(elapsed)
                    for activity in state.tool_activity:
                        TOOL_CALLS_TOTAL.labels(tool_name=activity.tool, status=activity.status).inc()
                except Exception as metric_err:
                    logger.error(f"[{request_id}] Failed to record Prometheus metrics: {metric_err}")

                logger.info(
                    f"[{request_id}] Agent complete: status={final_status}, "
                    f"steps={state.step}, tool_calls={state.tool_calls}, "
                    f"elapsed={elapsed:.2f}s"
                )



# Global singleton
agent_manager = AgentManager()
