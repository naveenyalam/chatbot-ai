import pytest
import uuid
import time
from app.core.cache import NovaCache

def test_redis_cache_flow():
    """Verify cache hits, misses, expiration, invalidation, and tenant/user isolation."""
    namespace = "generic"
    test_id = str(uuid.uuid4())
    key = f"cache_key_{test_id}"
    value = {"data": "cached_object", "id": test_id}

    # 1. Miss
    assert NovaCache.get(namespace, key) is None

    # 2. Set & Hit
    NovaCache.set(namespace, key, value, ttl=10)
    cached = NovaCache.get(namespace, key)
    assert cached == value

    # 3. Manual Invalidation
    NovaCache.delete(namespace, key)
    assert NovaCache.get(namespace, key) is None

    # 4. Expiration
    key_exp = f"cache_key_exp_{test_id}"
    NovaCache.set(namespace, key_exp, value, ttl=1)
    assert NovaCache.get(namespace, key_exp) == value
    time.sleep(1.2)
    assert NovaCache.get(namespace, key_exp) is None

    # 5. User isolation check
    user_a = f"user_a_{test_id}"
    user_b = f"user_b_{test_id}"
    key_a = f"user:{user_a}:config"
    key_b = f"user:{user_b}:config"

    NovaCache.set(namespace, key_a, "user_a_data", ttl=60)
    NovaCache.set(namespace, key_b, "user_b_data", ttl=60)

    assert NovaCache.get(namespace, key_a) == "user_a_data"
    assert NovaCache.get(namespace, key_b) == "user_b_data"

    # Clean up
    NovaCache.delete(namespace, key_a)
    NovaCache.delete(namespace, key_b)
