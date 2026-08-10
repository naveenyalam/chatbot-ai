import asyncio
import logging
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger("nova-ai.concurrency")

# Local asyncio Semaphores to limit concurrency within a single instance
SEMAPHORES = {
    "llm": asyncio.Semaphore(20),
    "agent": asyncio.Semaphore(5),
    "ingestion": asyncio.Semaphore(3),
    "embedding": asyncio.Semaphore(10),
    "code_exec": asyncio.Semaphore(2),
}

@asynccontextmanager
async def operation_limit(operation: str):
    """
    Limits local concurrency of an operation using asyncio semaphores.
    """
    sem = SEMAPHORES.get(operation)
    if not sem:
        sem = asyncio.Semaphore(10)
        SEMAPHORES[operation] = sem

    async with sem:
        yield

@asynccontextmanager
async def distributed_lock(lock_name: str, expire_seconds: int = 60, timeout_seconds: float = 10.0):
    """
    Acquires a distributed lock using Redis, falling back to local memory locks.
    """
    redis_client = get_redis_client()
    lock_key = f"nova:lock:{lock_name}"
    
    if redis_client:
        import uuid
        import time
        val = str(uuid.uuid4())
        acquired = False
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            # Set key with NX (not exists) and EX (expire)
            if redis_client.set(lock_key, val, ex=expire_seconds, nx=True):
                acquired = True
                break
            await asyncio.sleep(0.1)
            
        if not acquired:
            raise RuntimeError(f"Could not acquire distributed lock for '{lock_name}' within timeout.")
            
        try:
            yield
        finally:
            try:
                current_val = redis_client.get(lock_key)
                if current_val == val:
                    redis_client.delete(lock_key)
            except Exception as exc:
                logger.error(f"Failed to release Redis lock '{lock_name}': {exc}")
    else:
        # Fallback to local in-memory lock
        if not hasattr(distributed_lock, "_local_locks"):
            distributed_lock._local_locks = {}
        
        if lock_name not in distributed_lock._local_locks:
            distributed_lock._local_locks[lock_name] = asyncio.Lock()
            
        local_lock = distributed_lock._local_locks[lock_name]
        try:
            await asyncio.wait_for(local_lock.acquire(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Could not acquire local lock for '{lock_name}' within timeout.")
            
        try:
            yield
        finally:
            local_lock.release()
