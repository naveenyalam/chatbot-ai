import redis
import logging
import time
import threading
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("nova-ai.redis")

# ---------------------------------------------------------------------------
# Real Redis client (optional)
# ---------------------------------------------------------------------------
_redis_client = None
_redis_last_fail = 0.0
_redis_lock = threading.Lock()

# ---------------------------------------------------------------------------
# In-memory fallback cache
# ---------------------------------------------------------------------------
_mem_cache: dict[str, tuple[str, float]] = {}  # key -> (value, expires_at)
_mem_lock = threading.Lock()


def _mem_set(key: str, value: str, ttl_seconds: int) -> None:
    with _mem_lock:
        _mem_cache[key] = (value, time.time() + ttl_seconds)


def _mem_get(key: str) -> Optional[str]:
    with _mem_lock:
        entry = _mem_cache.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del _mem_cache[key]
            return None
        return value


def _mem_delete(key: str) -> None:
    with _mem_lock:
        _mem_cache.pop(key, None)


# ---------------------------------------------------------------------------
# Redis client helper
# ---------------------------------------------------------------------------
def get_redis_client() -> Optional[redis.Redis]:
    """
    Returns a live Redis client, or None if Redis is unavailable / not configured.
    Falls back gracefully — callers should use cache_set/cache_get instead.
    """
    global _redis_client, _redis_last_fail

    if not settings.REDIS_URL:
        return None

    with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        # Circuit-breaker: don't retry within 30 seconds of last failure
        if time.time() - _redis_last_fail < 30.0:
            return None

        try:
            client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=False,
            )
            client.ping()
            _redis_client = client
            logger.info("Successfully connected to Redis.")
            return _redis_client
        except Exception as exc:
            safe_url = (
                settings.REDIS_URL.split("@")[-1]
                if "@" in settings.REDIS_URL
                else settings.REDIS_URL.split("://")[-1]
            )
            logger.warning(
                f"Redis unavailable at {safe_url}: {exc}. Using in-memory fallback."
            )
            _redis_client = None
            _redis_last_fail = time.time()
            return None


# ---------------------------------------------------------------------------
# Public cache API — transparently uses Redis or in-memory fallback
# ---------------------------------------------------------------------------
def cache_set(key: str, value: str, ttl_seconds: int = 3600) -> bool:
    """Sets a cache entry. Falls back to in-memory if Redis is unavailable."""
    client = get_redis_client()
    status = "success"
    try:
        if client:
            client.setex(key, ttl_seconds, value)
        else:
            _mem_set(key, value, ttl_seconds)
        return True
    except Exception as exc:
        status = "error"
        logger.error(f"cache_set failed for key '{key}': {exc}")
        # Redis failed mid-op — save to memory as safety net
        try:
            _mem_set(key, value, ttl_seconds)
        except Exception:
            pass
        return False
    finally:
        _emit_metric("set", status)


def cache_get(key: str) -> Optional[str]:
    """Gets a cache entry. Falls back to in-memory if Redis is unavailable."""
    client = get_redis_client()
    status = "success"
    val = None
    try:
        if client:
            val = client.get(key)
        else:
            val = _mem_get(key)
        _emit_hit_miss(val)
        return val
    except Exception as exc:
        status = "error"
        logger.error(f"cache_get failed for key '{key}': {exc}")
        val = _mem_get(key)
        _emit_hit_miss(val)
        return val
    finally:
        _emit_metric("get", status)


def cache_delete(key: str) -> bool:
    """Deletes a cache entry from Redis and the in-memory store."""
    client = get_redis_client()
    status = "success"
    try:
        if client:
            client.delete(key)
        _mem_delete(key)  # always clear memory copy too
        return True
    except Exception as exc:
        status = "error"
        logger.error(f"cache_delete failed for key '{key}': {exc}")
        _mem_delete(key)
        return False
    finally:
        _emit_metric("delete", status)


# ---------------------------------------------------------------------------
# Internal metric helpers (soft-fail)
# ---------------------------------------------------------------------------
def _emit_metric(op_type: str, status: str) -> None:
    try:
        from app.core.metrics import REDIS_OPS_TOTAL
        REDIS_OPS_TOTAL.labels(op_type=op_type, status=status).inc()
    except Exception:
        pass


def _emit_hit_miss(val) -> None:
    try:
        from app.core.metrics import REDIS_CACHE_HITS_TOTAL, REDIS_CACHE_MISSES_TOTAL
        if val is not None:
            REDIS_CACHE_HITS_TOTAL.inc()
        else:
            REDIS_CACHE_MISSES_TOTAL.inc()
    except Exception:
        pass
