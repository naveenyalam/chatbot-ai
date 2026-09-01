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

    # 2. Fast Conversation Verification (Read-Only 1 row check or generate UUID)
    t_db0 = time.perf_counter()
    if conv_id:
        conv_obj = db.query(Conversation.id).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()
        if not conv_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found."
            )
    else:
        conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    first_prompt = chat_req.messages[-1].content if chat_req.messages else "New Chat"
    first_prompt_title = first_prompt[:50] + "..." if len(first_prompt) > 50 else first_prompt
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

    t_auth_ms = (t_redis0 - t_req_start) * 1000
    t_pre_llm_ms = (time.perf_counter() - t_req_start) * 1000
    t_llm_request_started_ms = t_pre_llm_ms
    logger.info(
        f"[PERF] request_id={request_id} request_received_ms=0.00 auth_ms={t_auth_ms:.2f} redis_ms={t_redis_ms:.2f} "
        f"database_ms={t_db_ms:.2f} context_ms={t_prompt_ms:.2f} router_ms=0.00 planner_ms=0.00 prompt_ms={t_prompt_ms:.2f} "
        f"pre_llm_ms={t_pre_llm_ms:.2f} llm_request_started_ms={t_llm_request_started_ms:.2f}"
    )

    async def event_generator():
        import json
        text_tokens = []
        web_citations = []
        first_token_time = None
        warning_emitted = False
        t_sse_start = time.perf_counter()
        sse_connection_ms = (t_sse_start - t_req_start) * 1000

        try:
            # Immediate SSE comment flush to open HTTP connection headers instantly across proxies
            yield ": ping\n\n"

            # Yield conversation ID first so frontend can bind state
            yield f"data: {json.dumps({'type': 'conversation_id', 'value': conv_id})}\n\n"

            # Yield complete latency breakdown metadata for production observability
            yield f"data: {json.dumps({'type': 'latency_breakdown', 'request_received_ms': 0.0, 'auth_ms': round(t_auth_ms, 2), 'redis_ms': round(t_redis_ms, 2), 'database_ms': round(t_db_ms, 2), 'context_ms': round(t_prompt_ms, 2), 'router_ms': 0.0, 'planner_ms': 0.0, 'prompt_ms': round(t_prompt_ms, 2), 'pre_llm_ms': round(t_pre_llm_ms, 2), 'llm_request_started_ms': round(t_llm_request_started_ms, 2), 'sse_connection_ms': round(sse_connection_ms, 2)})}\n\n"

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
                stream_gen = workspace_service.execute_workspace_chat(
                    request_id=request_id,
                    user_id=current_user.id,
                    conversation_id=conv_id,
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
                )
                stream_iter = stream_gen.__aiter__()

                while True:
                    if await request.is_disconnected():
                        logger.warning(f"[{request_id}] Client disconnected — stopping stream.")
                        break

                    now = time.perf_counter()
                    elapsed = now - t_req_start

                    # Phase 9: Failure safety check before LLM first content token
                    if first_token_time is None:
                        if elapsed >= 10.0:
                            logger.error(f"[{request_id}] Hard timeout: LLM first token exceeded 10s ({elapsed:.2f}s). Emitting clean failure event.")
                            yield f"data: {json.dumps({'type': 'error', 'code': 'FIRST_TOKEN_TIMEOUT', 'value': 'Request timed out waiting for AI model response (10s threshold). Please try again.'})}\n\n"
                            break
                        elif elapsed >= 8.0 and not warning_emitted:
                            warning_emitted = True
                            logger.warning(f"[{request_id}] Soft warning: LLM first token delayed past 8s ({elapsed:.2f}s). Emitting latency warning event.")
                            yield f"data: {json.dumps({'type': 'status', 'value': 'AI model is taking longer than expected to start streaming...'})}\n\n"

                    timeout_val = 0.5 if first_token_time is None else 60.0

                    try:
                        event = await asyncio.wait_for(stream_iter.__anext__(), timeout=timeout_val)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        continue

                    if event.get("type") == "text" and event.get("value"):
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                            ft_ms = (first_token_time - t_req_start) * 1000
                            logger.info(
                                f"[PERF] request_id={request_id} request_received_ms=0.00 auth_ms={t_auth_ms:.2f} redis_ms={t_redis_ms:.2f} "
                                f"database_ms={t_db_ms:.2f} context_ms={t_prompt_ms:.2f} router_ms=0.00 planner_ms=0.00 "
                                f"prompt_ms={t_prompt_ms:.2f} pre_llm_ms={t_pre_llm_ms:.2f} llm_request_started_ms={t_llm_request_started_ms:.2f} "
                                f"sse_connection_ms={sse_connection_ms:.2f} llm_first_token_ms={ft_ms:.2f} sse_first_content_token_ms={ft_ms:.2f}"
                            )
                            if ft_ms > settings.MAX_FIRST_TOKEN_LATENCY_SECONDS * 1000:
                                logger.warning(
                                    f"[LATENCY_GUARD_WARN] [{request_id}] LLM first token ({ft_ms:.2f}ms) "
                                    f"exceeded threshold of {settings.MAX_FIRST_TOKEN_LATENCY_SECONDS}s!"
                                )
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
                        # Ensure conversation exists
                        existing_conv = db_new.query(Conversation).filter(Conversation.id == conv_id).first()
                        if not existing_conv:
                            existing_conv = Conversation(
                                id=conv_id,
                                user_id=current_user.id,
                                title=first_prompt_title,
                                model=chat_req.model or "nova-intelligence",
                                workspace_mode=chat_req.workspace_mode or chat_req.mode or "general"
                            )
                            db_new.add(existing_conv)
                            db_new.flush()

                        assistant_msg = Message(
                            conversation_id=conv_id,
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

                        db_new.query(Conversation).filter(Conversation.id == conv_id).update({
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
