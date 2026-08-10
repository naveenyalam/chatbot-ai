import io
import asyncio
from PIL import Image
from app.services.search.provider import MockSearchProvider
from app.services.multimodal.provider import MockVisionProvider
from app.services.ai.router import route_ai_request
from app.schemas.chat import ChatMessage

def test_mock_search_provider():
    async def run():
        provider = MockSearchProvider()
        results = await provider.search("openai reasoning models")
        assert len(results) > 0
        assert any("openai" in r.title.lower() or "reasoning" in r.title.lower() for r in results)
    asyncio.run(run())

def test_mock_vision_provider():
    async def run():
        # Generate mock image bytes using Pillow
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        bytes_data = img_bytes.getvalue()
        
        provider = MockVisionProvider()
        res = await provider.analyze(bytes_data, "image/png", "diagram architecture details")
        assert "diagram" in res.lower() or "architecture" in res.lower()
    asyncio.run(run())

def test_router_dispatch(monkeypatch):
    async def run():
        # Mock basic session
        class MockDb:
            pass
            
        messages = [ChatMessage(role="user", content="Describe deep learning")]
        events = []
        
        # Patch ai_service.provider.stream to yield mock token chunks
        async def mock_stream(*args, **kwargs):
            yield "Deep learning is a subset of machine learning."

        from app.services.ai_service import ai_service
        monkeypatch.setattr(ai_service.provider, "stream", mock_stream)

        async for ev in route_ai_request(
            db=MockDb(),
            user_id="test-user",
            messages=messages,
            mode="normal",
            document_ids=[],
            model_alias=None,
            temperature=0.7
        ):
            events.append(ev)
            
        assert len(events) > 0
        assert any(ev.get("type") == "text" for ev in events)
    asyncio.run(run())
