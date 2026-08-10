import json
import logging
from fastapi import Request, Response
from app.core.redis import get_redis_client

logger = logging.getLogger("nova-ai.idempotency")

# Local memory cache for idempotency keys fallback
_local_idempotency = {}

def get_idempotency_key(request: Request) -> str | None:
    return request.headers.get("Idempotency-Key")

def check_idempotency(request: Request) -> Response | None:
    key = get_idempotency_key(request)
    if not key:
        return None
    
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached = redis_client.get(f"nova:idempotency:{key}")
            if cached:
                logger.info(f"Idempotency hit for key: {key}")
                data = json.loads(cached)
                return Response(
                    content=data.get("content"),
                    status_code=data.get("status_code"),
                    media_type=data.get("media_type")
                )
        except Exception as exc:
            logger.error(f"Failed to check Redis idempotency: {exc}")
    else:
        if key in _local_idempotency:
            logger.info(f"Idempotency hit (local memory) for key: {key}")
            data = _local_idempotency[key]
            return Response(
                content=data.get("content"),
                status_code=data.get("status_code"),
                media_type=data.get("media_type")
            )
    return None

def save_idempotency_response(request: Request, response_content: bytes, status_code: int, media_type: str = "application/json"):
    key = get_idempotency_key(request)
    if not key:
        return
    
    # Safely convert content to string
    if isinstance(response_content, bytes):
        content_str = response_content.decode("utf-8", errors="ignore")
    else:
        content_str = str(response_content)

    data = {
        "content": content_str,
        "status_code": status_code,
        "media_type": media_type
    }
    
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.setex(f"nova:idempotency:{key}", 86400, json.dumps(data))  # TTL 24 hours
        except Exception as exc:
            logger.error(f"Failed to save Redis idempotency: {exc}")
    else:
        _local_idempotency[key] = data
