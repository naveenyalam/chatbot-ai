import pytest
import uuid
import time
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.core.redis import get_redis_client

def test_redis_circuit_breaker_lifecycle():
    """Verify circuit breaker transitions CLOSED -> OPEN -> HALF_OPEN -> CLOSED via Redis."""
    provider_name = f"test_cb_prov_{uuid.uuid4().hex[:6]}"
    cb = CircuitBreaker(provider_name)
    cb.threshold = 2
    cb.cooldown = 1

    # 1. Initial CLOSED state
    assert cb.get_state() == "CLOSED"

    # 2. Record failures up to threshold -> OPEN
    cb.record_failure()
    assert cb.get_state() == "CLOSED"
    cb.record_failure()
    assert cb.get_state() == "OPEN"

    # 3. Blocked while OPEN
    with pytest.raises(CircuitBreakerOpenException):
        cb.check_call()

    # 4. Wait for cooldown -> HALF_OPEN
    time.sleep(1.2)
    assert cb.get_state() == "HALF_OPEN"

    # 5. Success -> resets to CLOSED
    cb.record_success()
    assert cb.get_state() == "CLOSED"

    # Clean up keys
    client = get_redis_client()
    if client:
        keys = cb._get_redis_keys()
        for k in keys.values():
            client.delete(k)
