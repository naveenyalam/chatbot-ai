import logging
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.chat import ChatMessage
from app.services.ai.chat import run_chat_pipeline
from app.services.ai.rag import run_rag_pipeline
from app.services.ai.web_search import run_web_search_pipeline
from app.services.ai.research import run_research_pipeline
from app.services.ai.multimodal import run_multimodal_pipeline

logger = logging.getLogger("nova-ai.ai.router")

async def route_ai_request(
    db: Session,
    user_id: str,
    messages: List[ChatMessage],
    mode: str | None,
    document_ids: List[str] | None,
    model_alias: str | None,
    temperature: float
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrates request routing across the multiple specialized pipeline agents.
    """
    resolved_mode = mode.lower() if mode else None
    doc_ids = document_ids or []
    
    # 1. Automatic mode detection fallback if mode is unspecified
    if not resolved_mode or resolved_mode == "normal":
        if doc_ids:
            # Check if there is an image in the document selection
            has_image = db.query(Document).filter(
                Document.id.in_(doc_ids),
                Document.user_id == user_id,
                Document.mime_type.like("image/%")
            ).first() is not None
            
            if has_image:
                resolved_mode = "multimodal"
            else:
                resolved_mode = "document_search"
        else:
            resolved_mode = "normal"
            
    logger.info(f"Routing request for user {user_id} with resolved_mode={resolved_mode}, model={model_alias}")
    
    # 2. Pipeline dispatching
    if resolved_mode == "web_search" or resolved_mode == "search":
        async for event in run_web_search_pipeline(
            messages=messages,
            model_alias=model_alias,
            temperature=temperature
        ):
            yield event
            
    elif resolved_mode == "deep_research" or resolved_mode == "research":
        async for event in run_research_pipeline(
            messages=messages,
            model_alias=model_alias,
            temperature=temperature
        ):
            yield event
            
    elif resolved_mode == "document_search" or resolved_mode == "document":
        async for event in run_rag_pipeline(
            db=db,
            user_id=user_id,
            messages=messages,
            document_ids=doc_ids,
            model_alias=model_alias,
            temperature=temperature
        ):
            yield event
            
    elif resolved_mode == "multimodal" or resolved_mode == "image":
        async for event in run_multimodal_pipeline(
            db=db,
            user_id=user_id,
            messages=messages,
            document_ids=doc_ids
        ):
            yield event
            
    else:
        # Standard chat fallback
        async for event in run_chat_pipeline(
            messages=messages,
            model_alias=model_alias,
            temperature=temperature
        ):
            yield event
