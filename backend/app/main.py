import logging
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.db.database import get_db
from app.core.config import settings
from app.api.routes import chat, auth, conversations, documents, workspace
from app.middleware.security import SecurityHeadersMiddleware, RequestSizeLimiterMiddleware
from app.core.logging_config import request_id_ctx

logger = logging.getLogger("nova-ai.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging config
    from app.core.logging_config import setup_logging
    setup_logging()
    
    logger.info("NOVA AI Core API starting up...")
    
    # Start background job worker
    from app.core.jobs import run_worker_in_background, stop_worker, register_job_handler
    
    async def process_document_job(payload: dict):
        from app.db.database import SessionLocal
        from app.services.document_service import process_document_in_background
        doc_id = payload.get("document_id")
        with SessionLocal() as db_session:
            await process_document_in_background(db_session, doc_id)

    register_job_handler("process_document", process_document_job)
    run_worker_in_background()

    # Seed demo user if not present
    try:
        from app.db.database import SessionLocal
        from app.models.user import User
        from app.services.auth_service import hash_password
        with SessionLocal() as db_session:
            demo_user = db_session.query(User).filter(User.email == "demo@nova.ai").first()
            if not demo_user:
                new_demo = User(
                    id="demo-user-id",
                    name="Demo Architect",
                    email="demo@nova.ai",
                    password_hash=hash_password("demo12345")
                )
                db_session.add(new_demo)
                db_session.commit()
                logger.info("Seeded demo user demo@nova.ai successfully.")
    except Exception as seed_err:
        logger.warning(f"Demo user seeding skipped: {seed_err}")

    yield
    
    logger.info("NOVA AI Core API shutting down...")
    
    # Stop background job worker
    try:
        stop_worker()
    except Exception as worker_err:
        logger.error(f"Error stopping background job worker: {worker_err}")
    
    # Graceful Database engine shutdown
    try:
        from app.db.database import engine
        if engine:
            engine.dispose()
            logger.info("Database connection pool disposed gracefully.")
    except Exception as db_err:
        logger.error(f"Error disposing database connections: {db_err}")
        
    # Graceful Redis client pool shutdown
    try:
        from app.core.redis import get_redis_client
        client = get_redis_client()
        if client:
            client.close()
            logger.info("Redis connection pool closed gracefully.")
    except Exception as redis_err:
        logger.error(f"Error closing Redis connections: {redis_err}")

    # Graceful background tasks cleanup
    try:
        pending = asyncio.all_tasks()
        pending = [t for t in pending if t is not asyncio.current_task()]
        if pending:
            logger.info(f"Cancelling {len(pending)} pending background tasks...")
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            logger.info("All background tasks finished or cancelled.")
    except Exception as task_err:
        logger.error(f"Error cancelling background tasks: {task_err}")

app = FastAPI(
    title="NOVA AI Core API",
    version="1.0.0",
    description="Asynchronous streaming FastAPI backend for NOVA AI Chat Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Config CORS origins dynamically based on settings
origins = settings.cors_origins
logger.info(f"Setting CORS origins to: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimiterMiddleware)

@app.middleware("http")
async def logging_and_correlation_middleware(request: Request, call_next):
    import uuid
    # Resolve correlation ID
    request_id = request.headers.get("X-Request-ID") or f"nova-{uuid.uuid4().hex[:12]}"
    
    token = request_id_ctx.set(request_id)
    request.state.request_id = request_id
    
    start_time = time.time()
    http_method = request.method
    endpoint = request.url.path
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        response.headers["X-Request-ID"] = request_id
        
        # Increment HTTP Prometheus metrics
        try:
            from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION
            HTTP_REQUESTS_TOTAL.labels(method=http_method, endpoint=endpoint, status_code=str(status_code)).inc()
            HTTP_REQUEST_DURATION.labels(method=http_method, endpoint=endpoint).observe(duration / 1000.0)
        except Exception:
            pass
            
        extra_fields = {
            "http_method": http_method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": round(duration, 2),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            extra_fields["user_id"] = user.id
            
        logger.info(
            f"HTTP {http_method} {endpoint} -> {status_code} ({round(duration, 2)}ms)",
            extra={"extra_fields": extra_fields}
        )
        return response
    except Exception as exc:
        duration = (time.time() - start_time) * 1000
        
        try:
            from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION
            HTTP_REQUESTS_TOTAL.labels(method=http_method, endpoint=endpoint, status_code="500").inc()
            HTTP_REQUEST_DURATION.labels(method=http_method, endpoint=endpoint).observe(duration / 1000.0)
        except Exception:
            pass
            
        extra_fields = {
            "http_method": http_method,
            "endpoint": endpoint,
            "status_code": 500,
            "duration_ms": round(duration, 2),
            "error": str(exc),
            "client_ip": request.client.host if request.client else "unknown"
        }
        logger.error(
            f"HTTP {http_method} {endpoint} failed: {exc}",
            exc_info=True,
            extra={"extra_fields": extra_fields}
        )
        raise exc
    finally:
        request_id_ctx.reset(token)

# Register custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Validation error: {exc.errors()}")
    from fastapi.encoders import jsonable_encoder
    errors_list = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=400,
        content={
            "detail": errors_list,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request contains invalid parameter inputs.",
                "request_id": request_id,
                "details": errors_list
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    error_msg = exc.detail
    if isinstance(error_msg, dict):
        detail_dict = dict(error_msg)
        if "error" not in detail_dict:
            detail_dict["error"] = {
                "code": "HTTP_EXCEPTION",
                "message": detail_dict.get("message") or "HTTP exception occurred.",
                "request_id": request_id
            }
        else:
            detail_dict["error"]["request_id"] = request_id
        if "detail" not in detail_dict:
            detail_dict["detail"] = detail_dict.get("message") or "HTTP exception occurred."
        return JSONResponse(status_code=exc.status_code, content=detail_dict, headers=exc.headers)
        
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "detail": exc.detail,
            "error": {
                "code": "HTTP_EXCEPTION",
                "message": str(exc.detail),
                "request_id": request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"[{request_id}] Unhandled exception: {exc}")
    message = "Something went wrong while executing your request."
    return JSONResponse(
        status_code=500,
        content={
            "detail": message,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "request_id": request_id
            }
        }
    )


# Register routes
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(workspace.router, prefix="/api", tags=["Workspace"])

def _safe_provider_status() -> dict:
    """Return safe AI provider status without exposing credentials."""
    ai_key_configured = bool(settings.AI_API_KEY and settings.AI_API_KEY.strip() not in ("", "your_llm_api_key_here"))
    return {
        "configured": ai_key_configured,
        "mode": "real" if ai_key_configured else "mock",
        "model": settings.AI_MODEL if ai_key_configured else None,
        "base_url": settings.AI_BASE_URL if ai_key_configured else None,
    }

@app.get("/health")
async def health():
    """Simple check that application process is alive. Includes safe AI provider status."""
    return {
        "status": "ok",
        "service": "nova-ai-backend",
        "ai_provider": _safe_provider_status(),
    }

@app.get("/api/health")
async def api_health():
    """Secondary API health endpoint with AI provider status."""
    return {
        "status": "ok",
        "service": "nova-ai-backend",
        "ai_provider": _safe_provider_status(),
    }

@app.get("/api/provider-status")
async def provider_status():
    """
    Safe endpoint to check AI provider configuration.
    Never exposes API key or credentials.
    """
    return {"ai_provider": _safe_provider_status()}

@app.get("/metrics")
async def metrics():
    """Exposes Prometheus metrics endpoint."""
    from fastapi import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/ready")
@app.get("/readiness")
async def readiness(db: Session = Depends(get_db)):
    """
    Readiness check endpoint that verifies connectivity to PostgreSQL and Redis.
    Returns 503 if critical dependencies are offline.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
        try:
            from app.core.metrics import DB_OPS_TOTAL
            DB_OPS_TOTAL.labels(op_type="ping", status="success").inc()
        except Exception:
            pass
    except Exception as exc:
        logger.error(f"Readiness check failed - Database error: {exc}")
        db_status = "error"
        try:
            from app.core.metrics import DB_OPS_TOTAL
            DB_OPS_TOTAL.labels(op_type="ping", status="error").inc()
        except Exception:
            pass

    redis_status = "ok"
    try:
        from app.core.redis import get_redis_client
        client = get_redis_client()
        if client:
            client.ping()
        else:
            if settings.ENV_MODE == "production":
                redis_status = "error"
            else:
                redis_status = "local-fallback"
    except Exception as exc:
        logger.error(f"Readiness check failed - Redis error: {exc}")
        redis_status = "error"

    if db_status == "error" or redis_status == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": db_status,
                "redis": redis_status
            }
        )

    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status
    }
