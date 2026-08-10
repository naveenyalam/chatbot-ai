import json
import logging
from typing import AsyncGenerator, Dict, Any, List
from app.schemas.chat import ChatMessage
from app.services.ai_service import ai_service, NOVA_SYSTEM_PROMPT
from app.services.search.provider import get_search_provider

logger = logging.getLogger("nova-ai.ai.research")

async def get_completion(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    tokens = []
    async for chunk in ai_service.provider.stream(messages, model, temperature):
        tokens.append(chunk)
    return "".join(tokens)

async def run_research_pipeline(
    messages: List[ChatMessage],
    model_alias: str | None,
    temperature: float
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Deep Research pipeline. Executes a multi-step query generation, searches subtopics,
    deduplicates citations, and streams a final consolidated report.
    """
    last_msg = messages[-1].content
    target_model = ai_service.provider.stream  # We can get target model name
    
    # Resolve target model identifier
    from app.core.config import settings
    model_name = settings.AI_MODEL
    if model_alias == "nova-fast":
        model_name = settings.AI_MODEL
    elif model_alias == "nova-reason":
        model_name = settings.AI_MODEL
        
    yield {"type": "status", "value": "planning", "query": "Formulating deep research strategy..."}
    
    # 1. Generate subtopics
    planning_prompt = (
        "You are the NOVA Deep Research Planner.\n"
        f"Based on the user's research request: \"{last_msg}\", generate exactly 3 distinct search subtopics "
        "to investigate. Return your response as a raw JSON array of strings, for example:\n"
        "[\"subtopic 1\", \"subtopic 2\", \"subtopic 3\"]\n"
        "Return ONLY the raw JSON array. Do not include markdown code block syntax."
    )
    
    subtopics = []
    try:
        raw_plan = await get_completion(
            messages=[{"role": "user", "content": planning_prompt}],
            model=model_name,
            temperature=0.3
        )
        # Parse JSON
        raw_plan_clean = raw_plan.strip().replace("```json", "").replace("```", "").strip()
        subtopics = json.loads(raw_plan_clean)
        if not isinstance(subtopics, list):
            subtopics = [f"{last_msg} detail 1", f"{last_msg} detail 2"]
    except Exception as err:
        logger.error(f"Failed to generate subtopics: {err}. Fallback to heuristics.")
        subtopics = [
            f"{last_msg} core background",
            f"{last_msg} current state and details",
            f"{last_msg} analysis and implications"
        ]

    # Let the UI know what the subtopics are
    yield {"type": "research_plan", "value": subtopics}
    
    # 2. Execute searches for each subtopic
    search_provider = get_search_provider()
    all_results = []
    seen_urls = set()
    
    for idx, subtopic in enumerate(subtopics[:3]):
        step_num = idx + 2
        yield {
            "type": "status",
            "value": "searching",
            "query": f"Step {step_num}/5: Gathering insights on '{subtopic}'..."
        }
        
        try:
            results = await search_provider.search(subtopic, max_results=3)
            for r in results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append(r)
        except Exception as e:
            logger.error(f"Search failed for subtopic {subtopic}: {e}")
            
    # Yield deduplicated citations
    citations = []
    context_blocks = []
    for idx, r in enumerate(all_results[:settings.RESEARCH_MAX_SOURCES]):
        c_num = idx + 1
        domain = r.url.split("/")[2] if r.url and len(r.url.split("/")) > 2 else "web"
        citations.append({
            "index": c_num,
            "title": r.title,
            "url": r.url,
            "domain": domain,
            "snippet": r.snippet,
            "published_at": r.published_at.isoformat() if r.published_at else None
        })
        context_blocks.append(
            f"--- START OF SOURCE #{c_num} ---\n"
            f"Title: {r.title}\n"
            f"URL: {r.url}\n"
            f"Content:\n{r.snippet}\n"
            f"--- END OF SOURCE #{c_num} ---"
        )
        
    yield {"type": "sources", "value": citations}
    
    # 3. Final synthesis
    yield {"type": "status", "value": "synthesizing", "query": "Step 5/5: Compiling final research report..."}
    
    synthesis_prompt = (
        f"{NOVA_SYSTEM_PROMPT.strip()}\n\n"
        "You are the NOVA Deep Research Agent. You have performed multi-step searches to compile a comprehensive report "
        f"on: \"{last_msg}\".\n"
        "Create a premium, highly structured, in-depth research report. Use markdown tables, bullet points, and headers.\n"
        "Cite facts from the sources below using numbered brackets, e.g. [1], [2].\n\n"
        "RESEARCH SOURCES:\n" + "\n\n".join(context_blocks)
    )
    
    payload_history = [ChatMessage(role="system", content=synthesis_prompt)] + messages[:-1] + [messages[-1]]
    
    async for chunk in ai_service.stream_chat(
        messages=payload_history,
        model_alias=model_alias,
        temperature=temperature
    ):
        yield {"type": "text", "value": chunk}
