import logging
from typing import List, Any
from sqlalchemy.orm import Session
from app.models.message import Message

logger = logging.getLogger("nova-ai.services.message_sync")

def sync_conversation_messages(db: Session, conversation_id: str, client_messages: List[Any]):
    """
    Synchronizes the database messages with the client's messages history
    to prevent duplicate user/assistant messages on edit, regenerate, or refresh.
    """
    try:
        # 1. Fetch existing messages sorted by created_at ascending
        db_msgs = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

        M = len(db_msgs)
        N = len(client_messages)

        logger.info(f"Syncing conversation {conversation_id}: DB count={M}, Client count={N}")

        # 2. If client history is shorter, truncate the DB messages
        if N < M:
            logger.info(f"Truncating database messages for conversation {conversation_id} from {M} to {N}")
            for db_msg in db_msgs[N:]:
                db.delete(db_msg)
            db.commit()
            # Reload messages list after deletion
            db_msgs = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()
            M = len(db_msgs)

        # 3. Update existing messages in-place if they differ
        for i in range(M):
            db_msg = db_msgs[i]
            client_msg = client_messages[i]
            
            # Extract content and role from client message (handles both dict and schema objects)
            client_content = client_msg.content if hasattr(client_msg, "content") else client_msg.get("content", "")
            client_role = client_msg.role if hasattr(client_msg, "role") else client_msg.get("role", "")

            if db_msg.content != client_content or db_msg.role != client_role:
                logger.info(f"Updating message in-place at index {i} for conversation {conversation_id}")
                db_msg.content = client_content
                db_msg.role = client_role
                db.add(db_msg)
        
        if M > 0:
            db.commit()

        # 4. Insert new messages that are not yet in the DB
        if M < N:
            logger.info(f"Appending {N - M} new client messages to DB for conversation {conversation_id}")
            from datetime import datetime, timedelta
            for i in range(M, N):
                client_msg = client_messages[i]
                client_content = client_msg.content if hasattr(client_msg, "content") else client_msg.get("content", "")
                client_role = client_msg.role if hasattr(client_msg, "role") else client_msg.get("role", "")
                
                new_db_msg = Message(
                    conversation_id=conversation_id,
                    role=client_role,
                    content=client_content,
                    status="complete",
                    created_at=datetime.utcnow() + timedelta(milliseconds=i)
                )
                db.add(new_db_msg)
            db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing conversation messages: {e}", exc_info=True)
        raise e
