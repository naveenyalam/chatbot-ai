import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.chat import ChatMessage
from app.services.multimodal.provider import get_multimodal_provider

logger = logging.getLogger("nova-ai.ai.multimodal")

async def run_multimodal_pipeline(
    db: Session,
    user_id: str,
    messages: List[ChatMessage],
    document_ids: List[str]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Multimodal pipeline. Finds image attachments, reads the file, runs analysis,
    and streams response chunks.
    """
    last_msg = messages[-1].content
    yield {"type": "status", "value": "analyzing", "query": "Processing image attachment..."}
    
    # 1. Retrieve image document meta
    image_doc = db.query(Document).filter(
        Document.id.in_(document_ids),
        Document.user_id == user_id,
        Document.mime_type.like("image/%")
    ).first()
    
    if not image_doc:
        yield {"type": "text", "value": "Error: No valid image attachment found. Please upload a PNG, JPG, or WEBP image."}
        return
        
    # 2. Read bytes and call vision provider
    try:
        with open(image_doc.storage_path, "rb") as f:
            image_bytes = f.read()
            
        provider = get_multimodal_provider()
        analysis = await provider.analyze(
            image_bytes=image_bytes,
            mime_type=image_doc.mime_type,
            prompt=last_msg
        )
        
        yield {"type": "status", "value": "synthesizing", "query": "Formulating analysis report..."}
        
        # 3. Stream analysis to mimic real-time generation
        words = analysis.split(" ")
        for word in words:
            yield {"type": "text", "value": word + " "}
            await asyncio.sleep(0.015)
            
    except Exception as exc:
        logger.exception(f"Multimodal analysis execution failed: {exc}")
        yield {"type": "text", "value": f"Error executing image analysis: {str(exc)}"}
