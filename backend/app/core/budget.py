import logging
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger("nova-ai.budget")

# Fallback local in-memory store
_local_budgets = {}

def _get_local_key(user_id: str, metric: str) -> str:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{user_id}:{metric}:{date_str}"

def _cleanup_local_budgets():
    # Keep memory clean by removing keys older than today
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    to_delete = [k for k in _local_budgets if not k.endswith(date_str)]
    for k in to_delete:
        del _local_budgets[k]

class UsageBudget:
    """
    Enforces user daily request caps and tracks token usage.
    """
    @staticmethod
    def check_request_budget(user_id: str):
        redis_client = get_redis_client()
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        limit = settings.MAX_DAILY_AI_REQUESTS

        if redis_client:
            key = f"nova:budget:{user_id}:requests:{date_str}"
            try:
                current = redis_client.get(key)
                if current and int(current) >= limit:
                    logger.warning(f"User {user_id} has exceeded daily AI request limit of {limit}")
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": {
                                "code": "BUDGET_EXCEEDED",
                                "message": "You have exceeded your daily AI request budget."
                            }
                        }
                    )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"Redis check_request_budget error: {exc}")
        else:
            _cleanup_local_budgets()
            key = _get_local_key(user_id, "requests")
            current = _local_budgets.get(key, 0)
            if current >= limit:
                logger.warning(f"User {user_id} has exceeded daily in-memory AI request limit of {limit}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": {
                            "code": "BUDGET_EXCEEDED",
                            "message": "You have exceeded your daily AI request budget."
                        }
                    }
                )

    @staticmethod
    def record_request(user_id: str, tokens_est: int = 0):
        redis_client = get_redis_client()
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Calculate seconds until end of day to set TTL
        now = datetime.utcnow()
        tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
        ttl = int((tomorrow - now).total_seconds())

        if redis_client:
            req_key = f"nova:budget:{user_id}:requests:{date_str}"
            tok_key = f"nova:budget:{user_id}:tokens:{date_str}"
            try:
                redis_client.incr(req_key)
                redis_client.expire(req_key, ttl)
                if tokens_est > 0:
                    redis_client.incrby(tok_key, tokens_est)
                    redis_client.expire(tok_key, ttl)
            except Exception as exc:
                logger.error(f"Redis record_request error: {exc}")
        else:
            _cleanup_local_budgets()
            req_key = _get_local_key(user_id, "requests")
            tok_key = _get_local_key(user_id, "tokens")
            
            _local_budgets[req_key] = _local_budgets.get(req_key, 0) + 1
            _local_budgets[tok_key] = _local_budgets.get(tok_key, 0) + tokens_est
