import pytest
import asyncio
import time
from app.services.redis_service import RedisService

@pytest.mark.asyncio
async def test_real_redis_operations():
    """Run E2E operations against the real Redis server."""
    # 1. Connect / Initialize
    RedisService.initialize()
    ping_ok = await RedisService.ping()
    if not ping_ok:
        pytest.skip("Real Redis server is not reachable locally — in-memory fallback active")

    key = "NOVA_TEST_KEY"
    val = "hello"

    # 2. SET
    set_ok = await RedisService.set(key, val, ttl_seconds=2)
    assert set_ok is True, "Failed to set test key in real Redis"

    # 3. GET & Verify Value
    get_val = await RedisService.get(key)
    assert get_val == val, f"Expected {val}, got {get_val}"

    # 4. EXISTS
    exists_ok = await RedisService.exists(key)
    assert exists_ok is True, "Key should exist in Redis"

    # 5. TTL
    val_ttl = await RedisService.ttl(key)
    assert val_ttl > 0, f"Expected TTL > 0, got {val_ttl}"

    # 6. Verify Expiration
    await asyncio.sleep(2.5)
    expired_val = await RedisService.get(key)
    assert expired_val is None, "Key should have expired"

    # 7. Re-SET for DELETE test
    await RedisService.set(key, val, ttl_seconds=60)
    
    # 8. DELETE
    del_ok = await RedisService.delete(key)
    assert del_ok is True, "Delete operation failed"

    # 9. Verify missing
    missing_val = await RedisService.get(key)
    assert missing_val is None, "Key should not exist after deletion"

    # 10. EXISTS after delete
    exists_post = await RedisService.exists(key)
    assert exists_post is False, "Key should not exist after deletion"
