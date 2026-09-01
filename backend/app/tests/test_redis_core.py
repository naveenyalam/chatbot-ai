import pytest
import uuid
import time
from app.core.redis import get_redis_client

def test_redis_core_operations():
    """Verify core Redis operations: SET, GET, DELETE, EXISTS, EXPIRE, TTL, INCR, HSET, HGET, HDEL."""
    client = get_redis_client()
    assert client is not None, "Redis server is offline"

    test_id = str(uuid.uuid4())
    key = f"nova:test:core:{test_id}"

    # 1. SET and GET
    assert client.set(key, "core_val") is True
    assert client.get(key) == "core_val"

    # 2. EXISTS
    assert client.exists(key) == 1

    # 3. EXPIRE and TTL
    assert client.expire(key, 10) is True
    ttl = client.ttl(key)
    assert 0 < ttl <= 10

    # 4. INCR
    counter_key = f"nova:test:counter:{test_id}"
    assert client.incr(counter_key) == 1
    assert client.incr(counter_key) == 2
    assert client.get(counter_key) == "2"

    # 5. Hash operations: HSET, HGET, HDEL
    hash_key = f"nova:test:hash:{test_id}"
    assert client.hset(hash_key, "field1", "val1") == 1
    assert client.hget(hash_key, "field1") == "val1"
    assert client.hdel(hash_key, "field1") == 1
    assert client.hget(hash_key, "field1") is None

    # 6. DELETE
    assert client.delete(key) == 1
    assert client.exists(key) == 0
    client.delete(counter_key)
    client.delete(hash_key)
