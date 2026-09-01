import pytest
import asyncio
import uuid
from app.core.redis import get_redis_client, cache_set, cache_get
from app.core.rate_limit import check_rate_limit
from app.core.circuit_breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_redis_concurrency_load():
    """Verify system stability under 20 simultaneous SET/GET operations, rate limit checks, and circuit-breaker failures."""
    client = get_redis_client()
    assert client is not None, "Redis server is offline"

    test_id = str(uuid.uuid4())

    # 1. 20 concurrent SET/GET
    async def set_get_task(idx):
        key = f"nova:test:concurrency:{test_id}:{idx}"
        # Since cache_set is synchronous, wrap in run_in_executor
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cache_set, key, f"val_{idx}", 10)
        val = await loop.run_in_executor(None, cache_get, key)
        assert val == f"val_{idx}"
        await loop.run_in_executor(None, client.delete, key)

    await asyncio.gather(*(set_get_task(i) for i in range(20)))

    # 2. 20 concurrent rate limit requests
    # Since check_rate_limit is synchronous, run in executor
    async def rate_task(idx):
        key = f"nova:test:rate_limit_concurrency:{test_id}"
        loop = asyncio.get_running_loop()
        allowed, _ = await loop.run_in_executor(None, check_rate_limit, key, 5, 10)
        return allowed

    results = await asyncio.gather(*(rate_task(i) for i in range(20)))
    # For a limit of 5 requests/window, exactly 5 should be allowed, others blocked
    assert results.count(True) == 5
    assert results.count(False) == 15

    # Clean up rate limit key
    client.delete(f"nova:development:rate_limit:nova:test:rate_limit_concurrency:{test_id}")

    # 3. Concurrent circuit breaker failures
    cb = CircuitBreaker(f"test_cb_concurrency_{test_id}")
    cb.threshold = 5
    cb.cooldown = 10

    async def cb_task():
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cb.record_failure)

    await asyncio.gather(*(cb_task() for _ in range(10)))
    assert cb.get_state() == "OPEN"

    # Clean up circuit keys
    keys = cb._get_redis_keys()
    for k in keys.values():
        client.delete(k)
