import asyncio
import json
import logging
from typing import Callable, Dict
from app.core.redis import get_redis_client

logger = logging.getLogger("nova-ai.jobs")

_local_queue = asyncio.Queue()
_registry = {}
_worker_task = None

def register_job_handler(name: str, handler: Callable):
    """Registers a handler for a specific job type."""
    _registry[name] = handler
    logger.info(f"Registered job handler for '{name}'")

async def enqueue_job(job_type: str, payload: dict):
    """
    Enqueue a background job using Redis list, falling back to local memory queue.
    """
    redis_client = get_redis_client()
    job_data = {
        "job_type": job_type,
        "payload": payload
    }
    
    if redis_client:
        try:
            redis_client.rpush("nova:jobs:queue", json.dumps(job_data))
            logger.info(f"Enqueued job '{job_type}' to Redis queue.")
            return
        except Exception as exc:
            logger.error(f"Redis enqueue_job failed: {exc}, falling back to local queue")
            
    await _local_queue.put(job_data)
    logger.info(f"Enqueued job '{job_type}' to local queue.")

async def start_job_worker():
    """
    Worker loop processing background jobs from Redis queue or local fallback.
    """
    logger.info("Starting background job worker loop...")
    while True:
        try:
            redis_client = get_redis_client()
            job_data = None
            
            if redis_client:
                try:
                    # BLPOP blocks; run in executor to avoid blocking the main event loop
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None, 
                        lambda: redis_client.blpop("nova:jobs:queue", timeout=1)
                    )
                    if result:
                        _, val = result
                        job_data = json.loads(val)
                except Exception as exc:
                    logger.error(f"Redis queue fetch error: {exc}")
            
            if not job_data:
                # Try local memory queue
                try:
                    job_data = await asyncio.wait_for(_local_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    pass
            
            if job_data:
                job_type = job_data.get("job_type")
                payload = job_data.get("payload", {})
                
                handler = _registry.get(job_type)
                if handler:
                    logger.info(f"Executing background job: {job_type}")
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(payload)
                        else:
                            await asyncio.get_event_loop().run_in_executor(None, handler, payload)
                        logger.info(f"Background job completed: {job_type}")
                    except Exception as exc:
                        logger.error(f"Background job '{job_type}' failed: {exc}", exc_info=True)
                else:
                    logger.warning(f"No handler registered for job type: {job_type}")
                    
        except asyncio.CancelledError:
            logger.info("Background job worker cancelled.")
            break
        except Exception as exc:
            logger.error(f"Error in background job worker: {exc}", exc_info=True)
            await asyncio.sleep(1)

def run_worker_in_background():
    """Starts the background worker task."""
    global _worker_task
    if _worker_task is None:
        _worker_task = asyncio.create_task(start_job_worker())
        logger.info("Background job worker task created.")

def stop_worker():
    """Stops the background worker task."""
    global _worker_task
    if _worker_task:
        _worker_task.cancel()
        _worker_task = None
        logger.info("Background job worker task stopped.")
