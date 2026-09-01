"""Research Agent — multi-source web research with citation accumulation."""
import logging
import time
from typing import AsyncGenerator, Dict, Any
from app.agents.base import BaseAgent
from app.agents.state import AgentState
from app.agents.policies import AgentPolicy
from app.services.model_router import model_router
from app.services.ai_service import NOVA_SYSTEM_PROMPT
from app.services.search.provider import get_search_provider

logger = logging.getLogger("nova-ai.agents.research")


class ResearchAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "research"

    def get_allowed_tools(self) -> set[str]:
        return AgentPolicy.allowed_tools("research")

    async def run(self, state: AgentState, db=None) -> AsyncGenerator[Dict[str, Any], None]:
        user_msg = state.messages[-1]["content"] if state.messages else ""
        AgentPolicy.check_all_limits(state)

        # Step 1: Plan subtopics
        state.step += 1
        yield {"type": "status", "value": "planning", "query": "Formulating research strategy..."}

        # Generate 3 subtopics via planner
        from app.agents.planner import AgentPlanner
        import json as _json

        planning_prompt = (
            f"User request: \"{user_msg}\"\n"
            "Generate exactly 3 targeted search queries to investigate this topic. "
            "Return ONLY a raw JSON array of strings, e.g.: [\"query 1\", \"query 2\", \"query 3\"]"
        )

        subtopics = []
        try:
            raw = await model_router.complete(
                [{"role": "user", "content": planning_prompt}],
                purpose="fast",
                temperature=0.2
            )
            raw = raw.strip().replace("```json", "").replace("```", "").strip()
            subtopics = _json.loads(raw)
            if not isinstance(subtopics, list):
                raise ValueError("Not a list")
        except Exception:
            subtopics = [
                f"{user_msg} overview",
                f"{user_msg} latest developments",
                f"{user_msg} analysis"
            ]

        yield {"type": "research_plan", "value": subtopics}

        # Step 2: Execute searches
        provider = get_search_provider()
        seen_urls = set()
        all_results = []

        for idx, subtopic in enumerate(subtopics[:3]):
            AgentPolicy.check_all_limits(state)
            state.step += 1
            state.tool_calls += 1
            step_num = idx + 2

            activity = state.add_tool_activity("web_search", f"Searching: {subtopic[:60]}")
            yield {"type": "tool_start", "tool": "web_search", "label": f"Step {step_num}: {subtopic[:60]}"}
            yield {"type": "status", "value": "searching", "query": f"Step {step_num}/5: {subtopic[:60]}..."}

            start = time.time()
            try:
                results = await provider.search(subtopic, max_results=3)
                elapsed = time.time() - start
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        all_results.append(r)
                state.mark_tool_complete(activity, elapsed, f"{len(results)} results")
                yield {"type": "tool_result", "tool": "web_search", "data": {"count": len(results)}, "success": True}
            except Exception as e:
                elapsed = time.time() - start
                state.mark_tool_failed(activity, elapsed)
                logger.error(f"Research search failed for '{subtopic}': {e}")

        # Build citations
        citations = []
        context_blocks = []
        for idx, r in enumerate(all_results[:12]):
            c_num = idx + 1
            domain = r.url.split("/")[2] if r.url and len(r.url.split("/")) > 2 else "web"
            citations.append({"index": c_num, "title": r.title, "url": r.url, "domain": domain,
                               "snippet": r.snippet, "published_at": r.published_at.isoformat() if r.published_at else None})
            context_blocks.append(
                f"[{c_num}] {r.title}\nURL: {r.url}\n{r.snippet}"
            )
            state.sources.append(citations[-1])

        if citations:
            yield {"type": "sources", "value": citations}

        # Step 3: Synthesize
        state.step += 1
        yield {"type": "status", "value": "synthesizing", "query": "Compiling research report..."}

        from app.services.workspace_prompts import get_multilingual_prompt
        multilingual_prompt = get_multilingual_prompt(user_msg, state.language)

        synthesis_system = (
            f"{multilingual_prompt}\n\n{NOVA_SYSTEM_PROMPT.strip()}\n\n"
            "You are the NOVA Research Agent. Write a comprehensive, structured research report.\n"
            "Use markdown headers, bullets, and tables where appropriate.\n"
            "Cite sources with numbered brackets [1], [2], etc.\n\n"
            "RESEARCH SOURCES:\n" + "\n\n".join(context_blocks)
        )

        payload = [{"role": "system", "content": synthesis_system}] + state.messages

        async for chunk in model_router.stream(payload, purpose="reasoning", temperature=state.temperature):
            yield {"type": "text", "value": chunk}
