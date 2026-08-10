"""Chat Agent — handles normal conversation with optional calculator access."""
import logging
from typing import AsyncGenerator, Dict, Any
from app.agents.base import BaseAgent
from app.agents.state import AgentState
from app.agents.policies import AgentPolicy
from app.services.model_router import model_router
from app.services.ai_service import NOVA_SYSTEM_PROMPT

logger = logging.getLogger("nova-ai.agents.chat")


class ChatAgent(BaseAgent):
    def __init__(self, mode: str = "normal"):
        super().__init__()
        self.mode = (mode or "normal").lower()

    @property
    def agent_type(self) -> str:
        return f"chat_{self.mode}" if self.mode != "normal" else "chat"

    def get_allowed_tools(self) -> set[str]:
        return AgentPolicy.allowed_tools("chat")

    def _get_system_prompt_for_mode(self) -> str:
        if self.mode in ("writing", "draft"):
            return (
                "You are NOVA AI Writing Specialist. You specialize in drafting, rewriting, summarizing, "
                "improving tone, and polishing prose. Focus on clarity, executive precision, and elegant structure "
                "without conversational preamble."
            )
        elif self.mode in ("coding", "code"):
            return (
                "You are NOVA AI Senior Software Architect. Provide production-grade, sandboxed code, debugging "
                "explanations, algorithm design, and unit tests. Always output clean Markdown code blocks with "
                "proper language tags. Never output malformed HTML or class attribute injection tags."
            )
        elif self.mode in ("data", "data-analysis"):
            return (
                "You are NOVA AI Data Analyst. You specialize in dataset statistical analysis, trend detection, "
                "CSV/JSON parsing, data cleaning scripts, and generating structured tabular reports."
            )
        return NOVA_SYSTEM_PROMPT.strip()

    async def run(self, state: AgentState, db=None) -> AsyncGenerator[Dict[str, Any], None]:
        """Direct chat execution with workspace-specific instructions and optional calculator access."""
        AgentPolicy.check_all_limits(state)
        state.step += 1

        user_msg = state.messages[-1]["content"] if state.messages else ""

        # Light heuristic: only call planner if message looks mathematical
        has_math = any(op in user_msg for op in ["+", "-", "*", "/", "%", "^", "**", "sqrt", "calculate", "compute"])
        allowed = self.get_allowed_tools()

        if has_math and allowed:
            plan = await self.planner.plan(user_msg, state.tool_results, allowed)
            if plan.action == "tool" and plan.tool_name == "calculator":
                activity = state.add_tool_activity("calculator", "Running calculation")
                yield {"type": "tool_start", "tool": "calculator", "label": "Running calculation"}
                state.tool_calls += 1
                import time
                start = time.time()
                try:
                    result = await self._execute_tool_with_retry(state, plan)
                    state.tool_results.append(result)
                    elapsed = time.time() - start
                    state.mark_tool_complete(activity, elapsed, str(result.get("data", {}).get("result", "")))
                    yield {"type": "tool_result", "tool": "calculator", "data": result["data"], "success": result["success"]}
                except Exception as e:
                    elapsed = time.time() - start
                    state.mark_tool_failed(activity, elapsed)
                    logger.warning(f"ChatAgent calculator failed: {e}")

        # Stream final response with workspace system prompt
        system_prompt = self._get_system_prompt_for_mode()
        if state.tool_results:
            tool_ctx = self._build_tool_context_message(state.tool_results)
            system_prompt += f"\n\nTool Results:\n{tool_ctx}"

        payload = [{"role": "system", "content": system_prompt}] + state.messages

        async for chunk in model_router.stream(payload, purpose="fast", temperature=0.7):
            yield {"type": "text", "value": chunk}

