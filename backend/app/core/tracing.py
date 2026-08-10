import time
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional

logger = logging.getLogger("nova-ai.tracing")

SENSITIVE_KEYS = {
    "password", "pass", "jwt", "token", "cookie", "authorization", 
    "api_key", "secret", "private_key", "prompt", "document", "payload"
}

def mask_attributes(attributes: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes dictionary values, removing PII, secrets, and raw prompt content.
    """
    if not attributes:
        return {}
    
    sanitized = {}
    for key, value in attributes.items():
        key_lower = str(key).lower()
        if any(s in key_lower for s in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized

@contextmanager
def trace_span(span_name: str, attributes: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
    """
    OpenTelemetry-compatible context manager for recording execution spans,
    latency timings, and correlation IDs without exposing PII.
    """
    start_time = time.time()
    clean_attrs = mask_attributes(attributes)
    req_id_str = f" [req_id={request_id}]" if request_id else ""
    
    logger.debug(f"Span START: '{span_name}'{req_id_str} | attrs: {clean_attrs}")
    try:
        yield
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000.0
        logger.error(f"Span ERROR: '{span_name}'{req_id_str} after {duration_ms:.2f}ms | error: {exc}")
        raise
    else:
        duration_ms = (time.time() - start_time) * 1000.0
        logger.debug(f"Span END: '{span_name}'{req_id_str} in {duration_ms:.2f}ms")
