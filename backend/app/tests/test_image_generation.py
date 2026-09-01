import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.image_intent_router import detect_image_intent
from app.services.image_provider import (
    NotConfiguredImageProvider,
    OpenAIImageProvider,
    ImageGenerationException,
    get_image_provider
)


def test_detect_image_intent_positive():
    prompts = [
        "Generate an image of a futuristic city",
        "Create a beautiful house surrounded by flowers",
        "Draw a robot working in a smart farm",
        "Make a picture of a sunset over mountains",
        "Generate a realistic image of a drone monitoring farmland",
        "generate a beautiful house with flowers, leaves and trees",
        "show me an image of a red dragon",
        "generate a photo of space station",
        "create a beautiful scenery",
        "draw a cat on a skateboard",
        "make an image of a cybernetic tiger",
        "/image a surrealist clock floating in space"
    ]
    for p in prompts:
        is_intent, extracted = detect_image_intent(p)
        assert is_intent is True, f"Failed to detect intent for prompt: {p}"
        assert len(extracted) > 0, f"Extracted prompt is empty for: {p}"


def test_detect_image_intent_negative():
    prompts = [
        "What is Python?",
        "Explain IoT",
        "How to generate an image in python using PIL?",
        "What is DALL-E and how does it work?",
        "Can you write code to draw a circle in canvas?"
    ]
    for p in prompts:
        is_intent, _ = detect_image_intent(p)
        assert is_intent is False, f"Erroneously detected intent for text prompt: {p}"


@pytest.mark.asyncio
async def test_not_configured_image_provider():
    provider = NotConfiguredImageProvider("Image generation is not configured. Please configure IMAGE_PROVIDER and the image API key.")
    with pytest.raises(ImageGenerationException) as exc_info:
        await provider.generate_image("a cute cat")
    assert exc_info.value.status_code == 503
    assert "Image generation is not configured" in exc_info.value.message


@pytest.mark.asyncio
async def test_openai_image_provider_success():
    provider = OpenAIImageProvider(api_key="sk-test-mock-key")
    
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "url": "https://oaidalleapiprodscus.blob.core.windows.net/test-image.png",
                "revised_prompt": "A beautiful modern house surrounded by blooming roses"
            }
        ]
    }

    with patch.object(provider, "_get_client") as mock_client_getter:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_getter.return_value = mock_client

        res = await provider.generate_image("a beautiful house")

        assert res["success"] is True
        assert res["image_url"] == "https://oaidalleapiprodscus.blob.core.windows.net/test-image.png"
        assert res["prompt"] == "a beautiful house"
        assert res["provider"] == "openai"


def test_images_generate_endpoint_validation():
    client = TestClient(app)

    # Missing authentication should return 401
    res = client.post("/api/images/generate", json={"prompt": "A scenic view"})
    assert res.status_code == 401


def test_proxy_download_security():
    client = TestClient(app)

    # Invalid protocol check
    res = client.get("/api/images/proxy-download?image_url=ftp://malicious-server/file.png")
    assert res.status_code in [400, 401]
