import abc
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("nova-ai.image-provider")


class ImageGenerationException(Exception):
    """Custom exception raised during image generation failures."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BaseImageProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an image asynchronously given a text prompt.
        """
        pass


class OpenAIImageProvider(BaseImageProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(60.0, connect=15.0)
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            self._client = httpx.AsyncClient(timeout=timeout, limits=limits)
        return self._client

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key.startswith("PLACEHOLDER") or self.api_key == "ollama":
            raise ImageGenerationException(
                "Cloud API key is missing or unconfigured for AI Image Generation.",
                status_code=503
            )

        client = await self._get_client()
        url = f"{self.base_url}/images/generations"
        target_model = model or settings.IMAGE_MODEL or "dall-e-3"

        # Validate size against DALL-E models
        allowed_sizes = ["1024x1024", "1024x1792", "1792x1024", "512x512", "256x256"]
        if size not in allowed_sizes:
            size = "1024x1024"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }

        # DALL-E-3 supports quality and style parameters
        if "dall-e-3" in target_model.lower():
            payload["quality"] = quality if quality in ["standard", "hd"] else "standard"
            payload["style"] = style if style in ["vivid", "natural"] else "vivid"

        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                error_detail = "Unknown error from image provider."
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", response.text)
                except Exception:
                    error_detail = response.text
                logger.error(f"OpenAI Image API error ({response.status_code}): {error_detail}")
                raise ImageGenerationException(
                    f"Image provider returned error: {error_detail}",
                    status_code=502 if response.status_code >= 500 else 400
                )

            res_data = response.json()
            data_list = res_data.get("data", [])
            if not data_list:
                raise ImageGenerationException("Image provider returned empty image dataset.", status_code=502)

            image_obj = data_list[0]
            image_url = image_obj.get("url")
            revised_prompt = image_obj.get("revised_prompt", prompt)

            if not image_url:
                raise ImageGenerationException("Image provider did not return a valid URL.", status_code=502)

            return {
                "success": True,
                "image_url": image_url,
                "prompt": prompt,
                "revised_prompt": revised_prompt,
                "provider": "openai",
                "model": target_model,
                "size": size
            }

        except httpx.TimeoutException:
            logger.error("Timeout connecting to OpenAI Image API")
            raise ImageGenerationException("Image generation request timed out. Please try again.", status_code=504)
        except httpx.RequestError as exc:
            logger.error(f"Network error contacting OpenAI Image API: {exc}")
            raise ImageGenerationException(f"Network error reaching image provider: {str(exc)}", status_code=503)


class PollinationsImageProvider(BaseImageProvider):
    def __init__(self, api_key: str = "pollinations-key"):
        self.api_key = api_key

    async def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: str = "standard",
        style: str = "vivid",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        import urllib.parse
        import random

        if not prompt or not prompt.strip():
            raise ImageGenerationException("Image generation prompt cannot be empty.", status_code=400)

        effective_prompt = prompt.strip()
        max_len = settings.IMAGE_GENERATION_MAX_PROMPT_LENGTH
        if len(effective_prompt) > max_len:
            effective_prompt = effective_prompt[:max_len]

        target_size = size or settings.IMAGE_SIZE or "1024x1024"
        try:
            width, height = map(int, target_size.split("x"))
        except Exception:
            width, height = 1024, 1024

        encoded_prompt = urllib.parse.quote(effective_prompt)
        seed = random.randint(1000, 999999)
        target_model = model or settings.IMAGE_MODEL or "flux"

        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"
        if model and model not in ("flux", "pollinations"):
            image_url += f"&model={model}"

        return {
            "success": True,
            "image_url": image_url,
            "prompt": prompt,
            "revised_prompt": effective_prompt,
            "provider": "pollinations",
            "model": target_model,
            "size": target_size
        }


class NotConfiguredImageProvider(BaseImageProvider):
    def __init__(self, reason: str = "Image generation is currently disabled or unconfigured."):
        self.reason = reason

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        raise ImageGenerationException(self.reason, status_code=503)


def get_image_provider() -> BaseImageProvider:
    if not settings.IMAGE_GENERATION_ENABLED:
        return NotConfiguredImageProvider("Image generation is not configured. Please configure IMAGE_PROVIDER and the image API key.")

    provider_name = settings.IMAGE_PROVIDER.lower()
    import os
    api_key = settings.IMAGE_API_KEY or settings.CLOUD_LLM_API_KEY or os.getenv("OPENAI_API_KEY") or (settings.AI_API_KEY if settings.AI_API_KEY != "ollama" else "")

    if provider_name == "pollinations":
        return PollinationsImageProvider(api_key=api_key or "pollinations_api_key_enabled")

    if provider_name == "openai" and api_key and api_key.startswith("sk-") and not api_key.startswith("sk-test"):
        base_url = settings.AI_BASE_URL if "openai.com" in settings.AI_BASE_URL else "https://api.openai.com/v1"
        return OpenAIImageProvider(api_key=api_key, base_url=base_url)

    # Default/Fallback to Pollinations image provider for reliable real AI image generation
    return PollinationsImageProvider(api_key=api_key or "pollinations_api_key_enabled")

