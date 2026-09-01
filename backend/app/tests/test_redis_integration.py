import pytest
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.redis_service import RedisService
from app.core.redis import (
    cache_set,
    cache_get,
    cache_delete,
    cache_delete_pattern,
    _mem_cache,
    _mem_lock
)
from app.core.config import settings

@pytest.mark.asyncio
async def test_redis_service_ping_success():
    """Verify ping returns True when Redis client responds with PONG."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = "PONG"
    
    # Reset cached ping result to force network check
    RedisService._last_ping_time = 0.0
    with patch.object(RedisService, "get_client", return_value=mock_client):
        is_healthy = await RedisService.ping()
        assert is_healthy is True
        assert RedisService._is_healthy is True

@pytest.mark.asyncio
async def test_redis_service_ping_failure():
    """Verify ping returns False when Redis client raises an exception."""
    mock_client = AsyncMock()
    mock_client.ping.side_effect = Exception("Connection refused")
    
    RedisService._last_ping_time = 0.0
    with patch.object(RedisService, "get_client", return_value=mock_client):
        is_healthy = await RedisService.ping()
        assert is_healthy is False
        assert RedisService._is_healthy is False

@pytest.mark.asyncio
async def test_redis_service_get_set_delete():
    """Verify get, set, delete async service helpers with mocked client."""
    mock_client = AsyncMock()
    mock_client.get.return_value = "value123"
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    
    with patch.object(RedisService, "get_client", return_value=mock_client):
        # 1. Test set
        set_ok = await RedisService.set("test_key", "value123", ttl_seconds=60)
        assert set_ok is True
        mock_client.setex.assert_called_once_with("test_key", 60, "value123")
        
        # 2. Test get
        val = await RedisService.get("test_key")
        assert val == "value123"
        mock_client.get.assert_called_once_with("test_key")
        
        # 3. Test delete
        del_ok = await RedisService.delete("test_key")
        assert del_ok is True
        mock_client.delete.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_redis_service_json_serialization():
    """Verify JSON helpers serialize and deserialize correctly."""
    mock_client = AsyncMock()
    test_dict = {"status": "ok", "count": 42}
    mock_client.get.return_value = json.dumps(test_dict)
    mock_client.set.return_value = True
    
    with patch.object(RedisService, "get_client", return_value=mock_client):
        # Test set_json
        set_ok = await RedisService.set_json("json_key", test_dict)
        assert set_ok is True
        mock_client.set.assert_called_once_with("json_key", json.dumps(test_dict))
        
        # Test get_json
        res = await RedisService.get_json("json_key")
        assert res == test_dict
        mock_client.get.assert_called_once_with("json_key")

def test_cache_fallback_behavior():
    """Verify synchronous cache set, get, delete fall back to memory when Redis is offline."""
    key = f"fallback_test_key_{int(time.time())}"
    val = {"data": "test_fallback"}
    
    with patch("app.core.redis.get_redis_client", return_value=None):
        # Clear memory cache first
        with _mem_lock:
            _mem_cache.pop(key, None)
            
        # 1. Set cache
        assert cache_set(key, json.dumps(val), ttl_seconds=10) is True
        
        # 2. Get cache
        cached = cache_get(key)
        assert cached is not None
        assert json.loads(cached) == val
        
        # 3. Delete cache
        assert cache_delete(key) is True
        assert cache_get(key) is None

def test_cache_delete_pattern_fallback():
    """Verify synchronous cache pattern deletion works in memory."""
    prefix = f"pattern_{int(time.time())}"
    key1 = f"{prefix}:key1"
    key2 = f"{prefix}:key2"
    key3 = f"other_prefix:key3"
    
    with patch("app.core.redis.get_redis_client", return_value=None):
        # Set keys
        cache_set(key1, "val1", ttl_seconds=10)
        cache_set(key2, "val2", ttl_seconds=10)
        cache_set(key3, "val3", ttl_seconds=10)
        
        # Invalidate pattern
        assert cache_delete_pattern(f"{prefix}:*") is True
        
        # Verify keys matching pattern are gone
        assert cache_get(key1) is None
        assert cache_get(key2) is None
        # Other prefix keys should remain
        assert cache_get(key3) == "val3"
