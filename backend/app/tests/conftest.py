import pytest
from app.core.redis import cache_delete_pattern
from app.core.rate_limit import _rate_limit_store, _rate_limit_lock

@pytest.fixture(autouse=True)
def clean_cache_and_limits():
    """Autouse fixture to clean Redis keys and in-memory rate limit/cache stores between tests."""
    # Reset in-memory rate limiter store
    with _rate_limit_lock:
        _rate_limit_store.clear()
    
    # Clean all test-related keys in Redis/memory cache
    # This covers 'nova:development:rate_limit:*', 'nova:development:cache:*', etc.
    cache_delete_pattern("nova:*")
    
    yield
    
    # Reset again after the test completes to ensure clean state
    with _rate_limit_lock:
        _rate_limit_store.clear()
    cache_delete_pattern("nova:*")
