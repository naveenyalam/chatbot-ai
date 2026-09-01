import pytest
from unittest.mock import patch
from app.core.redis import cache_set, cache_get, cache_delete, get_redis_client

def test_redis_failure_handling_and_recovery():
    """Verify that when Redis is mocked as offline, cache operations gracefully fall back to local memory and recover when restored."""
    # 1. Simulate Redis Offline
    with patch("app.core.redis.get_redis_client", return_value=None):
        # Operations should succeed using in-memory store
        assert cache_set("fail_key", "fail_val", ttl_seconds=10) is True
        assert cache_get("fail_key") == "fail_val"
        assert cache_delete("fail_key") is True
        assert cache_get("fail_key") is None

    # 2. Simulate Redis Online Recovery
    # Since Redis is actually running, we verify that operations now go to real Redis
    real_client = get_redis_client()
    if real_client:
        assert cache_set("recover_key", "recover_val", ttl_seconds=10) is True
        assert real_client.get("recover_key") == "recover_val"
        
        # Verify invalidation
        assert cache_delete("recover_key") is True
        assert real_client.get("recover_key") is None
