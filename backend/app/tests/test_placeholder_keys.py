import pytest
import asyncio
from app.core.config import settings
from app.services.ai_service import AIService
from app.services.model_router import ModelRouter
from app.services.llm_provider import NotConfiguredProvider
from app.core.errors import AIProviderNotConfiguredError
from app.schemas.chat import ChatMessage

pytestmark = pytest.mark.anyio

@pytest.mark.parametrize("placeholder_key", ["dummy-local-key", "your_llm_api_key_here", "", None])
async def test_placeholder_keys_not_configured(placeholder_key):
    """Verify that using any placeholder key results in NotConfiguredProvider and raises correct errors."""
    old_key = settings.AI_API_KEY
    old_mock = settings.AI_USE_MOCK
    
    settings.AI_API_KEY = placeholder_key
    settings.AI_USE_MOCK = False
    
    try:
        # Check settings
        assert not settings.ai_is_real, f"Key '{placeholder_key}' should not be considered real"
        
        # Check AIService
        service = AIService()
        assert isinstance(service.provider, NotConfiguredProvider)
        
        # Check ModelRouter
        router = ModelRouter()
        assert isinstance(router._provider, NotConfiguredProvider)
        
        # Verify streaming raises AIProviderNotConfiguredError
        with pytest.raises(AIProviderNotConfiguredError) as exc_info:
            async for _ in service.stream_chat(
                messages=[ChatMessage(role="user", content="hello")],
                model_alias="intelligence",
                temperature=0.7
            ):
                pass
        
        assert "AI_PROVIDER_NOT_CONFIGURED" in str(exc_info.value)
        assert "REAL AI PROVIDER NOT CONFIGURED" in exc_info.value.user_message
        
    finally:
        settings.AI_API_KEY = old_key
        settings.AI_USE_MOCK = old_mock
