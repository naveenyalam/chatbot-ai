import pytest
import asyncio
import uuid
import time
from datetime import datetime
from fastapi import HTTPException
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.core.budget import UsageBudget
from app.core.concurrency import SEMAPHORES, distributed_lock
from app.core.context import truncate_context_messages
from app.core.cache import NovaCache
from app.core.pagination import encode_cursor, decode_cursor
from app.core.config import settings
from app.schemas.chat import ChatMessage

def test_circuit_breaker_flow():
    provider_name = f"test_prov_{uuid.uuid4().hex[:6]}"
    cb = CircuitBreaker(provider_name)
    cb.threshold = 2
    cb.cooldown = 1

    # 1. Initial state should be CLOSED
    assert cb.get_state() == "CLOSED"

    # 2. Record failures up to threshold
    cb.record_failure()
    assert cb.get_state() == "CLOSED"
    cb.record_failure()
    assert cb.get_state() == "OPEN"

    # 3. Request should be blocked when OPEN
    with pytest.raises(CircuitBreakerOpenException):
        cb.check_call()

    # 4. Wait for cooldown to transition to HALF_OPEN
    time.sleep(1.1)
    assert cb.get_state() == "HALF_OPEN"

    # 5. Successful request resets to CLOSED
    cb.record_success()
    assert cb.get_state() == "CLOSED"

def test_usage_budget():
    user_id = f"test_user_budget_{uuid.uuid4().hex[:6]}"
    
    # Check initial budget passes
    UsageBudget.check_request_budget(user_id)
    
    # Record requests up to limit
    for _ in range(settings.MAX_DAILY_AI_REQUESTS):
        UsageBudget.record_request(user_id, tokens_est=50)
        
    # Next check should raise budget exception (429)
    with pytest.raises(HTTPException) as exc_info:
        UsageBudget.check_request_budget(user_id)
    assert exc_info.value.status_code == 429

def test_context_truncation():
    messages = [
        {"role": "system", "content": "You are a helpful AI."},
        {"role": "user", "content": "Hello 1"},
        {"role": "assistant", "content": "Hi 1"},
        {"role": "user", "content": "Hello 2"},
        {"role": "assistant", "content": "Hi 2"}
    ]
    # Restrict max chars to fit system prompt and last message only (approx 30 chars)
    truncated = truncate_context_messages(messages, max_chars=30)
    assert len(truncated) < len(messages)
    assert truncated[0]["role"] == "system"
    assert truncated[-1]["content"] == "Hi 2"

def test_nova_cache():
    key = f"test_key_{uuid.uuid4().hex[:6]}"
    NovaCache.set("generic", key, {"status": "ok"}, ttl=60)
    cached = NovaCache.get("generic", key)
    assert cached == {"status": "ok"}
    
    NovaCache.delete("generic", key)
    assert NovaCache.get("generic", key) is None

def test_cursor_encoding():
    now = datetime.now()
    cursor_str = encode_cursor(now, "rec_123")
    dt, rec_id = decode_cursor(cursor_str)
    assert rec_id == "rec_123"
    assert dt is not None

def test_concurrency_semaphores():
    async def run_check():
        async with SEMAPHORES["llm"]:
            assert SEMAPHORES["llm"].locked() or SEMAPHORES["llm"]._value < 20
    asyncio.run(run_check())

def test_distributed_lock_execution():
    async def run_lock():
        async with distributed_lock(f"test_lock_{uuid.uuid4().hex[:6]}"):
            assert True
    asyncio.run(run_lock())

def test_load_performance_simulation(monkeypatch):
    """Simulates 3 concurrent AI service requests to verify system stability."""
    from app.services.ai_service import ai_service
    
    async def mock_stream(*args, **kwargs):
        yield "Response chunk"

    monkeypatch.setattr(ai_service.provider, "stream", mock_stream)

    async def make_request(idx: int):
        chunks = []
        msg = ChatMessage(role="user", content=f"Load test request {idx}")
        async for chunk in ai_service.stream_chat(
            messages=[msg],
            model_alias="nova-fast",
            temperature=0.7
        ):
            chunks.append(chunk)
        return "".join(chunks)

    async def main():
        start = time.time()
        tasks = [make_request(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        assert len(results) == 3
        assert all(len(res) > 0 for res in results)
        assert elapsed < 10.0

    asyncio.run(main())
