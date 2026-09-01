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
    UsageBudget.check_request_budget(current_user.id)

    # Read request ID from request state for full-stack alignment
    request_id = getattr(request.state, "request_id", None) or f"nova-{uuid.uuid4().hex[:12]}"
    logger.info(f"[{request_id}] stream_chat: user={current_user.id}, mode={chat_req.mode}")

    conv_id = chat_req.conversation_id

    # 1. Verify access to existing conversation or create new one
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

    # 2. Save/sync user message
    if chat_req.messages:
        from app.services.message_sync import sync_conversation_messages
        try:
            sync_conversation_messages(db, conv.id, chat_req.messages)
        except Exception as exc:
            logger.error(f"[{request_id}] Failed to sync user messages: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to synchronize conversation history."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty."
        )


    # 3. Load recent history for context (up to 30 messages)
    db_messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.desc()).limit(30).all()
    # Reverse to restore chronological order
    db_messages.reverse()

    from app.core.context import truncate_context_messages, compress_old_messages
    ai_history = [
        {"role": m.role, "content": m.content}
        for m in db_messages
    ]
    ai_history = compress_old_messages(ai_history, keep_full_count=4)
    ai_history = truncate_context_messages(ai_history, max_chars=settings.MAX_TOKENS_PER_REQUEST * 4)

    async def event_generator():
        import json
        text_tokens = []
        web_citations = []

        try:
            # Yield conversation ID first so frontend can bind state
            yield f"data: {json.dumps({'type': 'conversation_id', 'value': conv.id})}\n\n"

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
                    text_tokens.append(event["value"])
                elif event.get("type") == "sources":
                    for citation in event.get("value", []):
                        if "url" in citation:
                            web_citations.append(citation)

                yield f"data: {json.dumps(event)}\n\n"

            # 4. Persist completed assistant message
            assistant_content = "".join(text_tokens)
            if assistant_content and not await request.is_disconnected():
                # Record daily usage budget (estimate tokens as chars // 4)
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

            # Surface AI provider configuration errors clearly to the frontend
            if "AI_PROVIDER_NOT_CONFIGURED" in err_str:
                user_message = "AI provider is not configured. Add a valid AI API key in backend/.env and restart NOVA AI."
                yield f"data: {json.dumps({'type': 'error', 'code': 'AI_PROVIDER_NOT_CONFIGURED', 'value': user_message})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'value': 'An unexpected error occurred. Please try again.'})}\n\n"

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.headers["X-Request-ID"] = request_id
    return response
