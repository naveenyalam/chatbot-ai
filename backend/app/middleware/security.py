import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger("nova-ai.middleware.security")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Appends standard OWASP security headers to all outgoing responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        
        # 1. Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 4. Restrict embedded features
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # 5. Strict Content Security Policy (allows local dev & self resources)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        
        # 6. Strict Transport Security (HSTS) - Enabled only in production/secure setups
        if settings.SECURE_COOKIES or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
            
        return response

class RequestSizeLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests exceeding the configured maximum size before reading the payload.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # We only enforce body limits on POST, PUT, PATCH, DELETE operations that contain payload bodies.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > settings.MAX_JSON_REQUEST_SIZE:
                        logger.warning(
                            f"Rejected oversized request from {request.client.host if request.client else 'unknown'}: "
                            f"{size} bytes (Limit: {settings.MAX_JSON_REQUEST_SIZE})"
                        )
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": {
                                    "code": "PAYLOAD_TOO_LARGE",
                                    "message": f"Request payload size exceeds maximum limit of {settings.MAX_JSON_REQUEST_SIZE} bytes."
                                }
                            }
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "INVALID_CONTENT_LENGTH",
                                "message": "Invalid Content-Length header."
                            }
                        }
                    )
        return await call_next(request)
