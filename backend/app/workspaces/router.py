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
    Unified workspace chat streaming endpoint.
    Routes requests according to workspace_id parameter, executes mode pipeline, and streams SSE events.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    workspace = workspace_registry.get_workspace(workspace_id)
    norm_mode = workspace.mode.value

    # Check user budget
    UsageBudget.check_request_budget(current_user.id)

    # 1. Resolve or create Conversation with workspace_mode attribute
    conv_id = chat_req.conversation_id
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        if not conv.workspace_mode or conv.workspace_mode != norm_mode:
            conv.workspace_mode = norm_mode
            db.commit()
    else:
        user_text = chat_req.message or (chat_req.messages[-1].content if chat_req.messages else "New Chat")
        title = user_text[:50] + "..." if len(user_text) > 50 else user_text
        try:
            conv = Conversation(
                user_id=current_user.id,
                title=title,
                model=chat_req.model or "nova-intelligence",
                workspace_mode=norm_mode
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
        except Exception as exc:
            db.rollback()
            logger.error(f"[{request_id}] Failed to create conversation: {exc}")
            raise HTTPException(status_code=500, detail="Failed to initialize chat session.")

    # 2. Sync conversation messages with frontend payload
    client_msgs = chat_req.messages
    if not client_msgs and chat_req.message:
        from app.workspaces.schemas import WorkspaceChatMessage
        client_msgs = [WorkspaceChatMessage(role="user", content=chat_req.message)]

    if client_msgs:
        from app.services.message_sync import sync_conversation_messages
        try:
            sync_conversation_messages(db, conv.id, client_msgs)
        except Exception as exc:
            logger.error(f"[{request_id}] Failed to sync user messages: {exc}")
            raise HTTPException(status_code=500, detail="Failed to synchronize conversation history.")
    else:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")


    # 3. Load conversation context
    db_messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at.desc()).limit(settings.MAX_CONTEXT_MESSAGES).all()
    db_messages.reverse()

    from app.core.context import truncate_context_messages
    ai_history = [{"role": m.role, "content": m.content} for m in db_messages]
    ai_history = truncate_context_messages(ai_history, max_chars=settings.MAX_TOKENS_PER_REQUEST * 4)

    async def event_generator():
        text_tokens = []
        web_citations = []
        try:
            yield f"data: {json.dumps({'type': 'conversation_id', 'value': conv.id})}\n\n"
            yield f"data: {json.dumps({'type': 'message_start'})}\n\n"

            # Check if user's prompt is requesting AI Image Generation
            last_prompt = chat_req.message or (chat_req.messages[-1].content if chat_req.messages else "")
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
                    conversation_id=conv.id,
                    messages=ai_history,
                    req=chat_req,
                    db=db
                ):
                    if await request.is_disconnected():
                        logger.warning(f"[{request_id}] Client disconnected from {workspace_id} stream.")
                        break

                    if event.get("type") == "text":
                        text_tokens.append(event["value"])
                    elif event.get("type") == "sources":
                        for citation in event.get("value", []):
                            if "url" in citation:
                                web_citations.append(citation)

                    yield f"data: {json.dumps(event)}\n\n"

            assistant_content = "".join(text_tokens)
            if assistant_content and not await request.is_disconnected():
                UsageBudget.record_request(current_user.id, len(assistant_content) // 4)
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

            yield f"data: {json.dumps({'type': 'message_complete'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            logger.exception(f"[{request_id}] Workspace execution error in {workspace_id}: {exc}")
            # Frontend SSE parser expects {"type": "error", "value": "string"}
            from app.core.errors import NOVABaseError
            user_msg = exc.user_message if isinstance(exc, NOVABaseError) else str(exc)
            err_event = {"type": "error", "value": user_msg}
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
