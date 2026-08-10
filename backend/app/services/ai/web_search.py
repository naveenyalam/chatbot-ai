import logging
from typing import AsyncGenerator, Dict, Any, List
from app.schemas.chat import ChatMessage
from app.services.ai_service import ai_service, NOVA_SYSTEM_PROMPT
from app.services.search.provider import get_search_provider

logger = logging.getLogger("nova-ai.ai.web-search")

async def run_web_search_pipeline(
    messages: List[ChatMessage],
    model_alias: str | None,
    temperature: float
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Web search pipeline. Searches web, builds isolated prompt context, and yields tokens.
    """
    last_msg = messages[-1].content
    yield {"type": "status", "value": "searching", "query": last_msg}
    
    citations = []
    try:
        provider = get_search_provider()
        search_results = await provider.search(last_msg, max_results=5)
        
        if search_results:
            context_blocks = []
            for idx, r in enumerate(search_results):
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
                
                # Enforce system boundaries to protect against prompt injection from search content
                context_blocks.append(
                    f"--- START OF UNTRUSTED SEARCH RESULT #{c_num} ---\n"
                    f"Title: {r.title}\n"
                    f"URL: {r.url}\n"
                    f"Content:\n{r.snippet}\n"
                    f"--- END OF UNTRUSTED SEARCH RESULT #{c_num} ---"
                )
            
            search_system_prompt = (
                f"{NOVA_SYSTEM_PROMPT.strip()}\n\n"
                "Answer the user's question using the provided web search context below. "
                "Synthesize findings objectively, cite facts, and provide clear structured markdown.\n"
                "Make sure to cite these search sources using numbered brackets, e.g. [1], [2], corresponding to the index.\n\n"
                "WEB SEARCH CONTEXT:\n" + "\n\n".join(context_blocks)
            )
            
            payload_history = [ChatMessage(role="system", content=search_system_prompt)] + messages[:-1] + [messages[-1]]
            
            # Emit citations list first
            yield {"type": "sources", "value": citations}
        else:
            payload_history = messages
            
    except Exception as err:
        logger.exception(f"Web search execution failed: {err}")
        payload_history = messages
        
    yield {"type": "status", "value": "synthesizing", "query": "Synthesizing search results..."}
    
    async for chunk in ai_service.stream_chat(
        messages=payload_history,
        model_alias=model_alias,
        temperature=temperature
    ):
        yield {"type": "text", "value": chunk}
