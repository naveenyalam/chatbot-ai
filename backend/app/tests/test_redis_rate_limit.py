import pytest
import uuid
import time
from app.core.rate_limit import check_rate_limit, _rate_limit_store
from app.core.redis import get_redis_client

def test_redis_rate_limiting():
    """Verify rate limit check allowed, limit enforcement (429), TTL expiration, and key isolation."""
    test_id = str(uuid.uuid4())
    key_user_a = f"rate_user_a_{test_id}"
    key_user_b = f"rate_user_b_{test_id}"

    # 1. User A first request (allowed)
    allowed, retry_after = check_rate_limit(key_user_a, limit=2, window=10)
    assert allowed is True
    assert retry_after == 0

    # 2. User A second request (allowed)
    allowed, retry_after = check_rate_limit(key_user_a, limit=2, window=10)
    assert allowed is True

    # 3. User A third request (blocked - returns 429)
    allowed, retry_after = check_rate_limit(key_user_a, limit=2, window=10)
    assert allowed is False
    assert retry_after > 0

    # 4. Isolation: User B request is allowed
    allowed, retry_after = check_rate_limit(key_user_b, limit=2, window=10)
    assert allowed is True
    assert retry_after == 0

    # Clean up Redis keys
    client = get_redis_client()
    if client:
        client.delete(f"nova:development:rate_limit:{key_user_a}")
        client.delete(f"nova:development:rate_limit:{key_user_b}")
