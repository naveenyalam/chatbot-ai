import json
import logging
from typing import Any, Optional
from cachetools import TTLCache
from app.core.redis import get_redis_client
from app.core.config import settings

from app.core.metrics import (
    REDIS_CACHE_HITS_TOTAL,
    REDIS_CACHE_MISSES_TOTAL,
    RAG_CACHE_HIT_TOTAL,
    RAG_CACHE_MISS_TOTAL
)

logger = logging.getLogger("nova-ai.cache")

# Fallback local in-memory caches per namespace
# Max size 1000 items, TTL 10 minutes (600 seconds)
_local_caches = {
    "rag": TTLCache(maxsize=1000, ttl=600),
    "routing": TTLCache(maxsize=1000, ttl=600),
    "embedding": TTLCache(maxsize=1000, ttl=600),
    "generic": TTLCache(maxsize=1000, ttl=600),
}

class NovaCache:
    """
    Unified caching wrapper supporting Redis with thread-safe/asyncio-safe local fallback.
    Supports namespaces: 'rag', 'routing', 'embedding', 'generic'.
    """

    @staticmethod
    def _get_key(namespace: str, key: str) -> str:
        return f"nova:{settings.ENV_MODE}:cache:{namespace}:{key}"


    @classmethod
    def get(cls, namespace: str, key: str) -> Optional[Any]:
        redis_client = get_redis_client()
        full_key = cls._get_key(namespace, key)

        if redis_client:
            try:
                val = redis_client.get(full_key)
                if val is not None:
                    # Increment hit metrics
                    REDIS_CACHE_HITS_TOTAL.inc()
                    if namespace == "rag":
                        RAG_CACHE_HIT_TOTAL.inc()
                    
                    try:
                        return json.loads(val)
                    except json.JSONDecodeError:
                        return val
            except Exception as exc:
                logger.error(f"Redis cache get error for '{full_key}': {exc}")
        
        # Fallback to local memory cache
        local_cache = _local_caches.get(namespace, _local_caches["generic"])
        if key in local_cache:
            # Increment hit metrics
            if namespace == "rag":
                RAG_CACHE_HIT_TOTAL.inc()
            else:
                REDIS_CACHE_HITS_TOTAL.inc()
            return local_cache[key]

        # Record miss metrics
        if namespace == "rag":
            RAG_CACHE_MISS_TOTAL.inc()
        else:
            REDIS_CACHE_MISSES_TOTAL.inc()
        return None

    @classmethod
    def set(cls, namespace: str, key: str, value: Any, ttl: int = 600) -> None:
        redis_client = get_redis_client()
        full_key = cls._get_key(namespace, key)

        if redis_client:
            try:
                serialized = json.dumps(value)
                redis_client.setex(full_key, ttl, serialized)
                return
            except Exception as exc:
                logger.error(f"Redis cache set error for '{full_key}': {exc}")

        # Fallback to local memory cache
        local_cache = _local_caches.get(namespace, _local_caches["generic"])
        local_cache[key] = value

    @classmethod
    def delete(cls, namespace: str, key: str) -> None:
        redis_client = get_redis_client()
        full_key = cls._get_key(namespace, key)

        if redis_client:
            try:
                redis_client.delete(full_key)
                return
            except Exception as exc:
                logger.error(f"Redis cache delete error for '{full_key}': {exc}")

        # Fallback to local memory cache
        local_cache = _local_caches.get(namespace, _local_caches["generic"])
        if key in local_cache:
            del local_cache[key]
