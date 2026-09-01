import asyncio
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatRequest, ChatMessage
from app.services.ai_service import ai_service
from app.services.auth_service import get_current_user

from app.core.rate_limit import RateLimiter
from app.core.config import settings
from app.core.budget import UsageBudget

logger = logging.getLogger("nova-ai.routes.chat")
router = APIRouter()

chat_limiter = RateLimiter(requests=settings.RATE_LIMIT_CHAT, window=60, key_prefix="chat")

@router.post("/stream", dependencies=[Depends(chat_limiter)])
async def stream_chat(
    chat_req: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    HTTP POST streaming endpoint yielding token chunks in SSE protocol.
    Requests are routed through AgentManager for bounded, observable execution.
    Every request receives a unique X-Request-ID header for traceability.
    """
    # Enforce user budget limits
    import time
    t_req_start = time.perf_counter()

    # 1. Redis budget check timing
    t_redis0 = time.perf_counter()
    UsageBudget.check_request_budget(current_user.id)
    t_redis_ms = (time.perf_counter() - t_redis0) * 1000

    request_id = getattr(request.state, "request_id", None) or f"nova-{uuid.uuid4().hex[:12]}"
    logger.info(f"[{request_id}] stream_chat: user={current_user.id}, mode={chat_req.mode}")

    conv_id = chat_req.conversation_id

    # 2. Database conversation check timing
    t_db0 = time.perf_counter()
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found."
            )
    else:
        first_prompt = chat_req.messages[-1].content if chat_req.messages else "New Chat"
        title = first_prompt[:50] + "..." if len(first_prompt) > 50 else first_prompt

        try:
            conv = Conversation(
                user_id=current_user.id,
                title=title,
                model=chat_req.model or "nova-intelligence"
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            logger.info(f"[{request_id}] Created new conversation {conv.id}")
        except Exception as exc:
            db.rollback()
            logger.error(f"[{request_id}] Failed to create conversation: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize chat session."
            )
    t_db_ms = (time.perf_counter() - t_db0) * 1000

    # 3. Fast In-Memory Context Construction (No redundant DB roundtrips)
    if not chat_req.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty."
        )

    t_prompt0 = time.perf_counter()
    raw_history = [{"role": m.role, "content": m.content} for m in chat_req.messages]
    bounded_history = raw_history[-12:] if len(raw_history) > 12 else raw_history

    from app.core.context import truncate_context_messages, compress_old_messages
    ai_history = compress_old_messages(bounded_history, keep_full_count=4)
    ai_history = truncate_context_messages(ai_history, max_chars=settings.MAX_TOKENS_PER_REQUEST * 4)
    t_prompt_ms = (time.perf_counter() - t_prompt0) * 1000

    t_pre_llm_ms = (time.perf_counter() - t_req_start) * 1000
    logger.info(
        f"[PERF] request_id={request_id} redis_ms={t_redis_ms:.2f} "
        f"database_ms={t_db_ms:.2f} prompt_ms={t_prompt_ms:.2f} pre_llm_ms={t_pre_llm_ms:.2f}"
    )

    async def event_generator():
        import json
        text_tokens = []
        web_citations = []
        first_token_time = None
        t_sse_start = time.perf_counter()

        try:
            # Immediate SSE comment flush to open HTTP connection headers instantly across proxies
            yield ": ping\n\n"

            # Yield conversation ID first so frontend can bind state
            yield f"data: {json.dumps({'type': 'conversation_id', 'value': conv.id})}\n\n"

            t_sse_first_event_ms = (time.perf_counter() - t_req_start) * 1000
            logger.info(f"[PERF] request_id={request_id} sse_first_event_ms={t_sse_first_event_ms:.2f}")

            # Check if user's prompt is requesting AI Image Generation
            last_prompt = chat_req.messages[-1].content if chat_req.messages else ""
            from app.services.image_intent_router import detect_image_intent
            is_image_req, image_prompt = detect_image_intent(last_prompt)

            if is_image_req:
                yield f"data: {json.dumps({'type': 'status', 'value': 'Generating AI image...'})}\n\n"
                from app.services.image_provider import get_image_provider, ImageGenerationException
                provider = get_image_provider()

                try:
                    res = await provider.generate_image(prompt=image_prompt)
                    img_url = res.get("image_url")
                    markdown_content = f"![AI Image: {image_prompt}]({img_url})"

                    yield f"data: {json.dumps({'type': 'image', 'image_url': img_url, 'prompt': image_prompt, 'status': 'complete', 'provider': res.get('provider', 'openai'), 'model': res.get('model', 'dall-e-3'), 'value': markdown_content})}\n\n"
                    text_tokens.append(markdown_content)
                except ImageGenerationException as img_exc:
                    err_msg = img_exc.message
                    yield f"data: {json.dumps({'type': 'error', 'value': err_msg})}\n\n"
                    text_tokens.append(err_msg)
            else:
                from app.services.workspace_service import workspace_service

                resolved_mode = chat_req.workspace_mode or chat_req.mode or "general"
                async for event in workspace_service.execute_workspace_chat(
                    request_id=request_id,
                    user_id=current_user.id,
                    conversation_id=conv.id,
                    messages=ai_history,
                    workspace_mode_raw=resolved_mode,
                    document_ids=chat_req.document_ids or [],
                    attachments=chat_req.attachments,
                    model_alias=chat_req.model,
                    temperature=chat_req.temperature,
                    db=db,
                    response_style=chat_req.response_style,
                    response_tone=chat_req.response_tone,
                    semantic_chunk_limit=chat_req.semantic_chunk_limit,
                    similarity_filtering=chat_req.similarity_filtering,
                    language=chat_req.language
                ):
                    if await request.is_disconnected():
                        logger.warning(f"[{request_id}] Client disconnected — stopping stream.")
                        break

                    if event.get("type") == "text":
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                            ft_ms = (first_token_time - t_req_start) * 1000
                            logger.info(f"[PERF] request_id={request_id} llm_first_token_ms={ft_ms:.2f}")
                        text_tokens.append(event["value"])
                    elif event.get("type") == "sources":
                        for citation in event.get("value", []):
                            if "url" in citation:
                                web_citations.append(citation)

                    yield f"data: {json.dumps(event)}\n\n"

            # 4. Persist user prompt & completed assistant message in single transaction post-stream
            assistant_content = "".join(text_tokens)
            total_req_ms = (time.perf_counter() - t_req_start) * 1000
            logger.info(f"[PERF] request_id={request_id} total_response_ms={total_req_ms:.2f} tokens_count={len(text_tokens)}")

            if assistant_content and not await request.is_disconnected():
                UsageBudget.record_request(current_user.id, len(assistant_content) // 4)
                try:
                    with SessionLocal() as db_new:
                        from datetime import datetime
                        assistant_msg = Message(
                            conversation_id=conv.id,
                            role="assistant",
                            content=assistant_content,
                            status="complete",
                            created_at=datetime.utcnow()
                        )
                        db_new.add(assistant_msg)
                        db_new.flush()

                        if web_citations:
                            from app.models.message import MessageSource
                            for cit in web_citations:
                                db_source = MessageSource(
                                    message_id=assistant_msg.id,
                                    title=cit.get("title", "Source"),
                                    url=cit.get("url", ""),
                                    domain=cit.get("domain", "web"),
                                    snippet=cit.get("snippet", ""),
                                    published_at=datetime.fromisoformat(cit["published_at"])
                                    if cit.get("published_at") else None
                                )
                                db_new.add(db_source)

                        db_new.query(Conversation).filter(Conversation.id == conv.id).update({
                            Conversation.updated_at: func.now()
                        })
                        db_new.commit()
                    logger.info(
                        f"[{request_id}] Persisted response "
                        f"({len(text_tokens)} tokens, {len(web_citations)} sources)."
                    )
                except Exception as db_exc:
                    logger.error(f"[{request_id}] Failed to write assistant message: {db_exc}")

            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            logger.warning(f"[{request_id}] Stream cancelled.")
        except Exception as exc:
            err_str = str(exc)
            logger.error(f"[{request_id}] Unhandled stream error: {exc}", exc_info=True)

            if "AI_PROVIDER_NOT_CONFIGURED" in err_str:
                user_message = "AI provider is not configured. Add a valid AI API key in backend/.env and restart NOVA AI."
                yield f"data: {json.dumps({'type': 'error', 'code': 'AI_PROVIDER_NOT_CONFIGURED', 'value': user_message})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'value': 'An unexpected error occurred. Please try again.'})}\n\n"

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-cache, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response
