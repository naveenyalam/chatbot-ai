import json
import logging
from typing import Any, Optional
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

logger = logging.getLogger("nova-ai.redis-service")

class RedisService:
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None
    _is_healthy: bool = False
    _last_ping_time: float = 0.0
    _cached_ping_result: bool = False
 
    @classmethod
    def get_client(cls) -> Optional[Redis]:
        if not settings.REDIS_URL:
            return None
        if cls._client is None:
            cls.initialize()
        return cls._client
 
    @classmethod
    def initialize(cls):
        if not settings.REDIS_URL:
            logger.info("[Redis] REDIS_URL not configured. Async Redis client disabled.")
            return
        
        try:
            logger.info("[Redis] Connecting...")
            pool_kwargs = {
                "decode_responses": True,
                "socket_timeout": settings.REDIS_TIMEOUT,
                "socket_connect_timeout": settings.REDIS_TIMEOUT,
            }
            if settings.REDIS_URL.startswith("rediss://"):
                pool_kwargs["ssl_cert_reqs"] = None

            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                **pool_kwargs
            )
            cls._client = Redis(connection_pool=cls._pool)
            cls._is_healthy = False
            logger.info("[Redis] Connected")
        except Exception as e:
            logger.error(f"[Redis] Connection failed: {e}")
            cls._client = None
            cls._pool = None
 
    @classmethod
    async def ping(cls) -> bool:
        import time
        now = time.time()
        if now - cls._last_ping_time < 5.0:
            return cls._cached_ping_result

        client = cls.get_client()
        if not client:
            cls._is_healthy = False
            cls._last_ping_time = now
            cls._cached_ping_result = False
            return False
        try:
            # redis-py async ping returns True on success
            res = await client.ping()
            cls._is_healthy = (res is True or res == "PONG" or res == b"PONG")
            cls._last_ping_time = now
            cls._cached_ping_result = cls._is_healthy
            if cls._is_healthy:
                logger.info("[Redis] Ping successful")
            else:
                logger.warning("[Redis] Ping did not return PONG")
            return cls._is_healthy
        except Exception as e:
            logger.error(f"[Redis] Connection lost: {e}")
            cls._is_healthy = False
            cls._last_ping_time = now
            cls._cached_ping_result = False
            return False


    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        client = cls.get_client()
        if not client:
            return None
        try:
            val = await client.get(key)
            if isinstance(val, bytes):
                return val.decode("utf-8")
            return val
        except Exception as e:
            logger.error(f"[Redis] Get failed for key '{key}': {e}")
            return None

    @classmethod
    async def set(cls, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            if ttl_seconds is not None:
                await client.setex(key, ttl_seconds, value)
            else:
                await client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"[Redis] Set failed for key '{key}': {e}")
            return False

    @classmethod
    async def delete(cls, key: str) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"[Redis] Delete failed for key '{key}': {e}")
            return False

    @classmethod
    async def exists(cls, key: str) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            res = await client.exists(key)
            return res > 0
        except Exception as e:
            logger.error(f"[Redis] Exists failed for key '{key}': {e}")
            return False

    @classmethod
    async def expire(cls, key: str, ttl_seconds: int) -> bool:
        client = cls.get_client()
        if not client:
            return False
        try:
            return await client.expire(key, ttl_seconds)
        except Exception as e:
            logger.error(f"[Redis] Expire failed for key '{key}': {e}")
            return False

    @classmethod
    async def ttl(cls, key: str) -> int:
        client = cls.get_client()
        if not client:
            return -2
        try:
            return await client.ttl(key)
        except Exception as e:
            logger.error(f"[Redis] Ttl failed for key '{key}': {e}")
            return -2

    @classmethod
    async def incr(cls, key: str) -> Optional[int]:
        client = cls.get_client()
        if not client:
            return None
        try:
            return await client.incr(key)
        except Exception as e:
            logger.error(f"[Redis] Incr failed for key '{key}': {e}")
            return None

    @classmethod
    async def get_json(cls, key: str) -> Optional[Any]:
        val = await cls.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            logger.error(f"[Redis] JSON decode failed for key '{key}'")
            return None

    @classmethod
    async def set_json(cls, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        try:
            serialized = json.dumps(value)
            return await cls.set(key, serialized, ttl_seconds)
        except Exception as e:
            logger.error(f"[Redis] JSON encode/set failed for key '{key}': {e}")
            return False

    @classmethod
    async def close(cls):
        logger.info("[Redis] Shutdown... Closing connections.")
        if cls._client:
            try:
                await cls._client.aclose()
            except Exception as e:
                logger.error(f"[Redis] Error closing client: {e}")
        if cls._pool:
            try:
                await cls._pool.disconnect()
            except Exception as e:
                logger.error(f"[Redis] Error disconnecting pool: {e}")
        cls._client = None
        cls._pool = None
        cls._is_healthy = False
        logger.info("[Redis] Shutdown complete")
