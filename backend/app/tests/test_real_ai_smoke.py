import pytest
from app.core.config import settings
from app.services.llm_provider import OpenAICompatibleProvider

pytestmark = pytest.mark.anyio

async def test_real_ai_smoke_connection():
    if not settings.ai_is_real:
        print("\nREAL AI TEST SKIPPED — AI_API_KEY NOT CONFIGURED")
        pytest.skip("REAL AI TEST SKIPPED — AI_API_KEY NOT CONFIGURED")
        
    provider = OpenAICompatibleProvider(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL)
    messages = [{"role": "user", "content": "Reply with exactly:\nREAL_AI_CONNECTION_OK"}]
    
    response_chunks = []
    async for chunk in provider.stream(messages, model=settings.AI_MODEL, temperature=0.0):
        response_chunks.append(chunk)
        
    full_text = "".join(response_chunks).strip()
    assert "REAL_AI_CONNECTION_OK" in full_text
