"""
Model Router — centralized abstraction for selecting and streaming from different models.

Removes hardcoded model names from pipeline code.
All model selection goes through this router.
"""
import logging
from typing import AsyncGenerator, List, Dict
from app.core.config import settings
from app.services.llm_provider import OpenAICompatibleProvider, NotConfiguredProvider, BaseLLMProvider

logger = logging.getLogger("nova-ai.model-router")

_PURPOSE_MAP = {
    "fast":      lambda: settings.FAST_CHAT_MODEL or settings.AI_FAST_MODEL or settings.AI_MODEL,
    "quality":   lambda: settings.QUALITY_CHAT_MODEL or settings.AI_MODEL,
    "reasoning": lambda: settings.AI_REASONING_MODEL or settings.QUALITY_CHAT_MODEL or settings.AI_MODEL,
    "vision":    lambda: settings.VISION_MODEL or settings.AI_MODEL,
    "default":   lambda: settings.AI_MODEL,
}


class ModelRouter:
    """
    Routes requests to the correct model based on the required purpose.
    Provides a unified streaming interface regardless of model type.
    Never silently falls back to a mock provider.
    """

    def __init__(self):
        if settings.AI_USE_MOCK:
            # Explicit mock mode (tests only)
            from app.services.llm_provider import MockLLMProvider
            logger.warning("ModelRouter: AI_USE_MOCK=true — using MockLLMProvider (tests only).")
            self._provider: BaseLLMProvider = MockLLMProvider()
        elif settings.ai_is_real:
            logger.info("ModelRouter: Using OpenAICompatibleProvider.")
            self._provider: BaseLLMProvider = OpenAICompatibleProvider(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL
            )
        else:
            logger.error(
                "ModelRouter: No real AI_API_KEY configured. "
                "Requests will fail until AI_API_KEY is set in backend/.env."
            )
            self._provider: BaseLLMProvider = NotConfiguredProvider()

    def get_model(self, purpose: str) -> str:
        """Return the model name for a given purpose."""
        resolver = _PURPOSE_MAP.get(purpose, _PURPOSE_MAP["default"])
        return resolver()

    async def stream(
        self,
        messages: List[Dict[str, str]],
        purpose: str = "default",
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from the model best suited to the given purpose.
        """
        model_name = self.get_model(purpose)
        logger.debug(f"ModelRouter routing to model='{model_name}' for purpose='{purpose}'")
        async for chunk in self._provider.stream(messages, model_name, temperature):
            yield chunk

    async def complete(
        self,
        messages: List[Dict[str, str]],
        purpose: str = "default",
        temperature: float = 0.3
    ) -> str:
        """
        Collect a full non-streaming completion. Used by planners and classifiers.
        """
        tokens = []
        async for chunk in self.stream(messages, purpose=purpose, temperature=temperature):
            tokens.append(chunk)
        return "".join(tokens)


# Global singleton
model_router = ModelRouter()
