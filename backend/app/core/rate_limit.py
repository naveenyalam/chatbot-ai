import time
import logging
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.core.config import settings

logger = logging.getLogger("nova-ai.rate-limit")

# Store in-memory request timestamps per key
# Key format: "prefix:identifier"
# Value: List of timestamps
_rate_limit_store: Dict[str, List[float]] = {}

def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    """
    Checks if the key is within the rate limit.
    Uses Redis sliding window if available, falling back to in-memory list tracking.
    Returns a tuple of (allowed, retry_after_seconds).
    """
    redis_status = "success"
    try:
        from app.core.redis import get_redis_client
        redis_client = get_redis_client()
        if redis_client:
            redis_key = f"rate_limit:{key}"
            now = time.time()
            pipe = redis_client.pipeline()
            # Add current request timestamp (using string representation of timestamp as member for uniqueness)
            pipe.zadd(redis_key, {str(now): now})
            # Remove timestamps older than window
            pipe.zremrangebyscore(redis_key, 0, now - window)
            # Count remaining timestamps
            pipe.zcard(redis_key)
            # Set key expiration to window size to save memory
            pipe.expire(redis_key, window)
            
            _, _, current_count, _ = pipe.execute()
            
            try:
                from app.core.metrics import REDIS_OPS_TOTAL
                REDIS_OPS_TOTAL.labels(op_type="rate_limit", status="success").inc()
            except Exception:
                pass
                
            if current_count <= limit:
                return True, 0
            else:
                oldest = redis_client.zrange(redis_key, 0, 0, withscores=True)
                retry_after = window
                if oldest:
                    _, oldest_score = oldest[0]
                    retry_after = int(max(1.0, (oldest_score + window) - now))
                return False, retry_after
    except Exception as exc:
        redis_status = "error"
        logger.error(f"Redis rate limiter exception, falling back to in-memory: {exc}")
        try:
            from app.core.metrics import REDIS_OPS_TOTAL
            REDIS_OPS_TOTAL.labels(op_type="rate_limit", status="error").inc()
        except Exception:
            pass


    # In-memory fallback
    now = time.time()
    history = _rate_limit_store.get(key, [])
    
    # Prune outdated timestamps
    history = [t for t in history if now - t < window]
    
    if len(history) >= limit:
        retry_after = window
        if history:
            retry_after = int(max(1.0, (history[0] + window) - now))
        return False, retry_after
        
    history.append(now)
    _rate_limit_store[key] = history
    return True, 0

class RateLimiter:
    """
    FastAPI dependency for route rate-limiting.
    """
    def __init__(self, requests: int | None = None, window: int | None = None, key_prefix: str = "global"):
        self.requests = requests if requests is not None else settings.RATE_LIMIT_REQUESTS
        self.window = window if window is not None else settings.RATE_LIMIT_WINDOW_SECONDS
        self.key_prefix = key_prefix

    async def __call__(self, request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return

        # Determine identifier:
        # Check if user is authenticated (read from cookie/header)
        identifier = "anonymous"
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                
        if token:
            from app.services.auth_service import decode_access_token
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                identifier = payload["sub"]

        # Fallback to IP if anonymous
        if identifier == "anonymous":
            identifier = request.client.host if request.client else "unknown"

        key = f"{self.key_prefix}:{identifier}"
        
        allowed, retry_after = check_rate_limit(key, self.requests, self.window)
        if not allowed:
            logger.warning(f"Rate limit hit for key: {key} (Limit: {self.requests}/{self.window}s)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Please try again in {retry_after} seconds."
                    }
                },
                headers={"Retry-After": str(retry_after)}
            )
