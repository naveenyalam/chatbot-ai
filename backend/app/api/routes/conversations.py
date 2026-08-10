import logging
from typing import List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationRename, ConversationResponse, MessageResponse
from app.services.auth_service import get_current_user
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.core.pagination import paginate_query

logger = logging.getLogger("nova-ai.routes.conversations")

general_limiter = RateLimiter(
    requests=settings.RATE_LIMIT_GENERAL,
    window=settings.RATE_LIMIT_WINDOW_SECONDS,
    key_prefix="general"
)

router = APIRouter(dependencies=[Depends(general_limiter)])

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    response: Response,
    limit: int = 20,
    cursor: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations belonging to the authenticated user.
    Sorted in descending order of last activity (updated_at DESC).
    Prefetches relations via joinedload and paginates via cursor.
    """
    query = db.query(Conversation).options(joinedload(Conversation.user)).filter(
        Conversation.user_id == current_user.id
    )
    
    paginated_results, next_cursor = paginate_query(
        query=query,
        model_class=Conversation,
        limit=limit,
        cursor=cursor
    )
    
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
        
    return paginated_results

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation instance for the authenticated user.
    """
    try:
        # Default placeholder title if not specified
        title = conv_req.title or "New Conversation"
        model = conv_req.model or "nova-intelligence"

        new_conv = Conversation(
            user_id=current_user.id,
            title=title,
            model=model
        )
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)

        logger.info(f"Created conversation {new_conv.id} for user {current_user.id}")
        return new_conv
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to create conversation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize new conversation."
        )

@router.get("/search", response_model=List[ConversationResponse])
async def search_conversations(
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full-text search across conversation titles and message content for current user.
    """
    if not q or len(q.strip()) < 2:
        return []
    
    search_term = f"%{q.strip()}%"
    matching_conv_ids = db.query(Message.conversation_id).filter(
        Message.content.ilike(search_term)
    ).distinct()
    
    results = db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        (Conversation.title.ilike(search_term) | Conversation.id.in_(matching_conv_ids))
    ).order_by(Conversation.updated_at.desc()).limit(limit).all()
    
    return results

@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve details of a specific conversation, validating user ownership.
    """
    conv = db.query(Conversation).options(joinedload(Conversation.user)).filter(Conversation.id == id).first()
    
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    return conv

@router.post("/{id}/generate-title", response_model=ConversationResponse)
async def generate_conversation_title(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a concise 3-6 word conversation title using AI based on the first user message.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    first_msg = db.query(Message).filter(
        Message.conversation_id == id,
        Message.role == "user"
    ).order_by(Message.created_at.asc()).first()
    
    if not first_msg or not first_msg.content:
        return conv
        
    from app.services.ai_service import ai_service
    title_prompt = f"Summarize the following user request into a concise title of 3 to 6 words. Do not use quotes or punctuation.\n\nUser request: {first_msg.content[:300]}"
    
    try:
        raw_title = await ai_service.generate_response(
            prompt=title_prompt,
            system_prompt="You generate ultra-concise, title-case topic labels (3-6 words max) for chat sessions. Respond only with the title.",
            temperature=0.3
        )
        clean_title = raw_title.strip().strip('"\'').strip('.')
        if clean_title and len(clean_title) > 2:
            conv.title = clean_title[:80]
            db.commit()
            db.refresh(conv)
    except Exception as exc:
        logger.warning(f"AI title generation failed for conv {id}: {exc}")
        
    return conv

@router.delete("/{id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific message from a conversation, validating ownership.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    msg = db.query(Message).filter(Message.id == message_id, Message.conversation_id == id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")
        
    try:
        db.delete(msg)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to delete message {message_id}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to delete message.")

@router.patch("/{id}", response_model=ConversationResponse)
async def rename_conversation(
    id: str,
    rename_req: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rename a conversation, validating ownership.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    try:
        conv.title = rename_req.title
        db.commit()
        db.refresh(conv)
        logger.info(f"Renamed conversation {conv.id} to '{conv.title}'")
        return conv
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to rename conversation {id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rename conversation."
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation instance, validating ownership. Cascade delete handles message records.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    try:
        db.delete(conv)
        db.commit()
        logger.info(f"Deleted conversation {id} for user {current_user.id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to delete conversation {id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation."
        )

@router.get("/{id}/messages", response_model=List[MessageResponse])
async def list_messages(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve message logs chronologically for a specific conversation.
    """
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    # Sort messages chronologically by created_at (Section 13 requirement)
    messages = db.query(Message).filter(
        Message.conversation_id == id
    ).order_by(Message.created_at.asc()).all()

    return messages
