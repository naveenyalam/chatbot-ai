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
        from app.services.workspace_prompts import get_workspace_prompt
        return get_workspace_prompt(self.mode)

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
        from app.services.workspace_prompts import get_multilingual_prompt
        multilingual_prompt = get_multilingual_prompt(user_msg, state.language)
        system_prompt = f"{multilingual_prompt}\n\n{self._get_system_prompt_for_mode()}"
        if state.tool_results:
            tool_ctx = self._build_tool_context_message(state.tool_results)
            system_prompt += f"\n\nTool Results:\n{tool_ctx}"

        # Inject style/tone guidelines
        style_instructions = ""
        if state.response_style == "concise":
            style_instructions += "\n- Write in a highly concise, direct manner. Use short bullet points and omit fluff."
        elif state.response_style == "detailed":
            style_instructions += "\n- Provide a highly in-depth, detailed explanation with full context."
        if state.response_tone == "friendly":
            style_instructions += "\n- Keep your tone warm, friendly, and conversational."
        elif state.response_tone == "technical":
            style_instructions += "\n- Maintain a strictly academic, professional, and code-heavy tone."
        if style_instructions:
            system_prompt += f"\n\n### RESPONSE STYLE & TONE GUIDELINES{style_instructions}"

        formatted_messages = []
        for i, msg in enumerate(state.messages):
            m = dict(msg)
            if i == len(state.messages) - 1 and state.language:
                lang_clean = state.language.strip().lower()
                if lang_clean not in ("auto", "auto detect", ""):
                    lang_map = {
                        "en": "English", "english": "English",
                        "te": "Telugu", "telugu": "Telugu",
                        "hi": "Hindi", "hindi": "Hindi",
                        "kn": "Kannada", "kannada": "Kannada",
                        "ta": "Tamil", "tamil": "Tamil"
                    }
                    target = lang_map.get(lang_clean, state.language)
                    m["content"] = f"{m.get('content', '')}\n\n[Respond ONLY in {target} and its native script]"
            formatted_messages.append(m)

        payload = [{"role": "system", "content": system_prompt}] + formatted_messages

        async for chunk in model_router.stream(payload, purpose="fast", temperature=state.temperature):
            yield {"type": "text", "value": chunk}
