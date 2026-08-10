import json
import logging
import contextvars
from datetime import datetime, timezone
from app.core.config import settings

# Thread/async-safe context variable to store request correlation ID
request_id_ctx = contextvars.ContextVar("request_id", default="-")

class StructuredJsonFormatter(logging.Formatter):
    """
    Formatter that outputs single-line JSON log messages for production log collection.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName
        }

        # Safe extraction of extra fields (excluding sensitive authentication keys)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                if k not in ["password", "token", "access_token", "api_key", "secret", "jwt", "authorization"]:
                    log_data[k] = v

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

class ReadableDevFormatter(logging.Formatter):
    """
    Human-readable console log formatter for local development environments.
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        req_id = request_id_ctx.get()
        req_part = f" [{req_id}]" if req_id and req_id != "-" else ""
        
        msg = f"{timestamp} [{record.levelname}] [{record.name}]{req_part}: {record.getMessage()}"

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            safe_extra = {k: v for k, v in record.extra_fields.items() if k not in ["password", "token", "access_token", "api_key", "secret", "jwt"]}
            if safe_extra:
                msg += f" | Extra: {safe_extra}"

        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"

        return msg

def setup_logging():
    """
    Sets up the global logging configuration based on settings.ENV_MODE.
    """
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    
    if settings.ENV_MODE == "production":
        handler.setFormatter(StructuredJsonFormatter())
        root_logger.setLevel(logging.INFO)
    else:
        handler.setFormatter(ReadableDevFormatter())
        root_logger.setLevel(logging.INFO)
        
    root_logger.addHandler(handler)
    
    # Mute noisy internal frameworks loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
