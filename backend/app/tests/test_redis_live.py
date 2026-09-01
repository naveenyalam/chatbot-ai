import pytest
from app.core.redis import get_redis_client

def test_live_redis_connection():
    """Verify live connection to localhost:6379 returns True on ping."""
    client = get_redis_client()
    assert client is not None, "Real Redis server is not running on localhost:6379"
    assert client.ping() is True
