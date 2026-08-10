from typing import AsyncGenerator, Dict, Any, List
from app.schemas.chat import ChatMessage
from app.services.ai_service import ai_service

async def run_chat_pipeline(
    messages: List[ChatMessage],
    model_alias: str | None,
    temperature: float
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Standard chat generation yielding text token events.
    """
    async for chunk in ai_service.stream_chat(
        messages=messages,
        model_alias=model_alias,
        temperature=temperature
    ):
        yield {"type": "text", "value": chunk}
