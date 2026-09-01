import pytest
from app.core.config import settings
from app.services.llm_provider import OpenAICompatibleProvider

pytestmark = pytest.mark.anyio

@pytest.mark.skipif(not settings.ai_is_real, reason="REAL_AI_NOT_CONFIGURED")
class TestRealProviderLive:
    async def test_real_provider_live_python_explain(self):
        # This test calls the real provider directly.
        provider = OpenAICompatibleProvider(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL)
        messages = [{"role": "user", "content": "Explain what Python is in two sentences."}]
        
        response_chunks = []
        async for chunk in provider.stream(messages, model=settings.AI_MODEL, temperature=0.3):
            response_chunks.append(chunk)
            
        full_text = "".join(response_chunks).strip()
        assert len(full_text) > 0, "Response must not be empty"
        assert "python" in full_text.lower(), "Response must mention python"

    async def test_real_provider_live_prime_code(self):
        provider = OpenAICompatibleProvider(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL)
        messages = [{"role": "user", "content": "Write a Python program to check whether a number is prime."}]
        
        response_chunks = []
        async for chunk in provider.stream(messages, model=settings.AI_MODEL, temperature=0.3):
            response_chunks.append(chunk)
            
        full_text = "".join(response_chunks).strip()
        assert len(full_text) > 0, "Response must not be empty"
        assert "def " in full_text, "Response must contain a real code block or definition"
        assert "prime" in full_text.lower(), "Response must reference prime numbers"
