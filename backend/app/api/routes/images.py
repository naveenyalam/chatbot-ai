import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
import httpx

from app.core.config import settings
from app.api.routes.auth import get_current_user
from app.services.image_provider import get_image_provider, ImageGenerationException
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger("nova-ai.images-api")

router = APIRouter(prefix="/images", tags=["Image Generation"])


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Text description of the image to generate")
    size: Optional[str] = Field(default="1024x1024", description="Output resolution (e.g. 1024x1024)")
    quality: Optional[str] = Field(default="standard", description="Image quality (standard or hd)")
    style: Optional[str] = Field(default="vivid", description="Visual style (vivid or natural)")


@router.post("/generate")
async def generate_image(
    req: GenerateImageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an AI image using the configured production cloud image provider.
    """
    if not settings.IMAGE_GENERATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Image Generation is currently disabled on this server."
        )

    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty."
        )

    if len(clean_prompt) > settings.IMAGE_GENERATION_MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prompt exceeds maximum length of {settings.IMAGE_GENERATION_MAX_PROMPT_LENGTH} characters."
        )

    # Rate limiting protection
    user_id = current_user.get("user_id", "anonymous")
    rate_ok = await check_rate_limit(
        f"image_gen:{user_id}",
        max_requests=settings.IMAGE_GENERATION_RATE_LIMIT,
        window_seconds=60
    )
    if not rate_ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have reached the image generation rate limit. Please wait a minute before generating more images."
        )

    provider = get_image_provider()
    try:
        result = await provider.generate_image(
            prompt=clean_prompt,
            size=req.size or "1024x1024",
            quality=req.quality or "standard",
            style=req.style or "vivid"
        )
        return result
    except ImageGenerationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.exception("Unexpected error during image generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during image generation: {str(exc)}"
        )


@router.get("/proxy-download")
async def proxy_download_image(
    image_url: str = Query(..., description="The URL of the image to download"),
    filename: Optional[str] = Query(default="nova_ai_image.png", description="Filename for attachment"),
    current_user: dict = Depends(get_current_user)
):
    """
    Secure server-side download proxy to prevent CORS issues when downloading provider image URLs.
    """
    if not image_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image URL protocol.")

    # Restrict proxying to trusted image host domains or standard HTTPS image URLs
    allowed_domains = ["oaidalleapiprodscus.blob.core.windows.net", "openai.com", "replicate.delivery", "upstash.io"]
    is_allowed = any(domain in image_url for domain in allowed_domains) or image_url.startswith("https://")

    if not is_allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image URL domain is not permitted for proxy download.")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(image_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch image from provider storage.")

            content_type = resp.headers.get("content-type", "image/png")
            safe_filename = filename.replace('"', '').replace("'", "")

            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
            )
    except Exception as exc:
        logger.error(f"Failed to proxy download image from {image_url}: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to download image file.")
