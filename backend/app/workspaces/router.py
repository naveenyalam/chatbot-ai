import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db, SessionLocal
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.config import settings
from app.core.budget import UsageBudget

from app.workspaces.enums import WorkspaceMode
from app.workspaces.schemas import (
    WorkspaceMetadata,
    WorkspaceListResponse,
    WorkspaceChatRequest,
    WorkspaceValidationResult
)
from app.workspaces.registry import workspace_registry

logger = logging.getLogger("nova-ai.workspaces.router")

router = APIRouter()


@router.get("/workspaces", response_model=WorkspaceListResponse)
def list_workspaces():
    """List metadata, capabilities, and suggested prompts for all 7 workspace modes."""
    return WorkspaceListResponse(workspaces=workspace_registry.list_workspaces())


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceMetadata)
def get_workspace_detail(workspace_id: str):
    """Get metadata details for a specific workspace mode."""
    workspace = workspace_registry.get_workspace(workspace_id)
    return workspace.metadata


@router.post("/workspaces/{workspace_id}/validate", response_model=WorkspaceValidationResult)
def validate_workspace_payload(workspace_id: str, req: WorkspaceChatRequest):
    """Validate a request payload for a specific workspace mode."""
    workspace = workspace_registry.get_workspace(workspace_id)
    warnings = workspace.validate_request(req)
    return WorkspaceValidationResult(
        valid=True,
        workspace_mode=workspace.mode.value,
        warnings=warnings
    )


@router.post("/workspaces/{workspace_id}/chat")
async def workspace_chat_stream(
    workspace_id: str,
    chat_req: WorkspaceChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unified workspace chat streaming endpoint optimized for ultra-fast TTFT.
    In-memory context preparation with deferred post-stream database persistence.
    """
    import time
    import uuid
    t_req_start = time.perf_counter()

    request_id = getattr(request.state, "request_id", None) or f"nova-{uuid.uuid4().hex[:12]}"
    workspace = workspace_registry.get_workspace(workspace_id)
    norm_mode = workspace.mode.value

    # 1. Fast Redis Budget Check
    t_redis0 = time.perf_counter()
    UsageBudget.check_request_budget(current_user.id)
    t_redis_ms = (time.perf_counter() - t_redis0) * 1000

    # 2. Fast Conversation Verification (Read-Only 1 row check or generate UUID)
    t_db0 = time.perf_counter()
    conv_id = chat_req.conversation_id
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if not conv.workspace_mode or conv.workspace_mode != norm_mode:
            conv.workspace_mode = norm_mode
            db.commit()
    else:
        conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    t_db_ms = (time.perf_counter() - t_db0) * 1000

    # 3. Fast In-Memory Context Construction (No pre-LLM DB sync or re-queries)
    t_prompt0 = time.perf_counter()
    client_msgs = chat_req.messages or []
    if not client_msgs and chat_req.message:
        from app.workspaces.schemas import WorkspaceChatMessage
        client_msgs = [WorkspaceChatMessage(role="user", content=chat_req.message)]

    if not client_msgs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    raw_history = [
        {"role": (m.role if hasattr(m, "role") else m.get("role")),
         "content": (m.content if hasattr(m, "content") else m.get("content", ""))}
        for m in client_msgs
    ]
    bounded_history = raw_history[-12:] if len(raw_history) > 12 else raw_history

    from app.core.context import truncate_context_messages, compress_old_messages
    ai_history = compress_old_messages(bounded_history, keep_full_count=4)
    ai_history = truncate_context_messages(ai_history, max_chars=settings.MAX_TOKENS_PER_REQUEST * 4)
    t_prompt_ms = (time.perf_counter() - t_prompt0) * 1000

    t_auth_ms = (t_redis0 - t_req_start) * 1000
    t_pre_llm_ms = (time.perf_counter() - t_req_start) * 1000
    logger.info(
        f"[PERF] request_id={request_id} auth_ms={t_auth_ms:.2f} redis_ms={t_redis_ms:.2f} "
        f"database_ms={t_db_ms:.2f} context_ms={t_prompt_ms:.2f} rag_ms=0.00 prompt_ms={t_prompt_ms:.2f} pre_llm_ms={t_pre_llm_ms:.2f}"
    )

    user_text = chat_req.message or (client_msgs[-1].content if hasattr(client_msgs[-1], "content") else client_msgs[-1].get("content", ""))
    first_prompt_title = user_text[:50] + "..." if len(user_text) > 50 else user_text

    async def event_generator():
        text_tokens = []
        web_citations = []
        first_token_time = None

        try:
            # Immediate HTTP stream ping flush across proxies
            yield ": ping\n\n"

            yield f"data: {json.dumps({'type': 'conversation_id', 'value': conv_id})}\n\n"
            yield f"data: {json.dumps({'type': 'message_start'})}\n\n"

            t_sse_first_event_ms = (time.perf_counter() - t_req_start) * 1000
            logger.info(f"[PERF] request_id={request_id} sse_first_event_ms={t_sse_first_event_ms:.2f}")

            # Check if user's prompt is requesting AI Image Generation
            from app.services.image_intent_router import detect_image_intent
            is_image_req, image_prompt = detect_image_intent(user_text)

            if is_image_req:
                yield f"data: {json.dumps({'type': 'status', 'value': 'Generating AI image...'})}\n\n"
                from app.services.image_provider import get_image_provider, ImageGenerationException
                provider = get_image_provider()

                try:
                    res = await provider.generate_image(prompt=image_prompt)
                    img_url = res.get("image_url")
                    markdown_content = f"![AI Image: {image_prompt}]({img_url})"

                    yield f"data: {json.dumps({'type': 'image', 'image_url': img_url, 'prompt': image_prompt, 'status': 'complete', 'provider': res.get('provider', 'pollinations'), 'model': res.get('model', 'pollinations'), 'value': markdown_content})}\n\n"
                    text_tokens.append(markdown_content)
                except ImageGenerationException as img_exc:
                    err_msg = img_exc.message
                    yield f"data: {json.dumps({'type': 'error', 'value': err_msg})}\n\n"
                    text_tokens.append(err_msg)
            else:
                async for event in workspace.execute_stream(
                    request_id=request_id,
                    user_id=current_user.id,
                    conversation_id=conv_id,
                    messages=ai_history,
                    req=chat_req,
                    db=db
                ):
                    if await request.is_disconnected():
                        logger.warning(f"[{request_id}] Client disconnected from {workspace_id} stream.")
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

            # Post-Stream Single Database Transaction for Messages & Conversation Sync
            assistant_content = "".join(text_tokens)
            total_req_ms = (time.perf_counter() - t_req_start) * 1000
            logger.info(f"[PERF] request_id={request_id} total_response_ms={total_req_ms:.2f} tokens_count={len(text_tokens)}")

            if assistant_content and not await request.is_disconnected():
                UsageBudget.record_request(current_user.id, len(assistant_content) // 4)
                try:
                    with SessionLocal() as db_new:
                        # 1. Ensure conversation exists in DB
                        existing_conv = db_new.query(Conversation).filter(Conversation.id == conv_id).first()
                        if not existing_conv:
                            existing_conv = Conversation(
                                id=conv_id,
                                user_id=current_user.id,
                                title=first_prompt_title,
                                model=chat_req.model or "nova-intelligence",
                                workspace_mode=norm_mode
                            )
                            db_new.add(existing_conv)
                            db_new.flush()

                        # 2. Sync client messages into DB
                        from app.services.message_sync import sync_conversation_messages
                        sync_conversation_messages(db_new, conv_id, client_msgs)

                        # 3. Add completed assistant message
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
                except Exception as db_exc:
                    logger.error(f"[{request_id}] Failed to commit post-stream conversation state: {db_exc}")

            yield f"data: {json.dumps({'type': 'message_complete'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            logger.exception(f"[{request_id}] Workspace execution error in {workspace_id}: {exc}")
            from app.core.errors import NOVABaseError
            user_msg = exc.user_message if isinstance(exc, NOVABaseError) else str(exc)
            err_event = {"type": "error", "value": user_msg}
            yield f"data: {json.dumps(err_event)}\n\n"

    response = StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["Cache-Control"] = "no-cache, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response
