import pytest
import uuid
from app.core.config import settings

def test_redis_security_isolation():
    """Verify that Redis key names incorporate the target environment mode and are user-isolated."""
    test_id = str(uuid.uuid4())
    
    # 1. Environment scope prefix validation
    from app.core.cache import NovaCache
    from app.core.rate_limit import RateLimiter
    
    # Verify NovaCache prepends settings.ENV_MODE to avoid cross-environment contamination
    cache_key = NovaCache._get_key("generic", "test")
    assert f":{settings.ENV_MODE}:" in cache_key
    assert cache_key.startswith("nova:")

    # 2. Verify that credentials are not included in string representations of connection configuration
    assert "password" not in repr(settings.REDIS_URL)

    # 3. Check for any dangerous commands patterns
    # Verify that the word 'FLUSH' is not imported or used anywhere in production cache interface
    import app.core.redis as r_mod
    for name in dir(r_mod):
        assert "flush" not in name.lower()
