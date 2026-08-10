import base64
import json
from datetime import datetime
from typing import Tuple, Optional, Any
from sqlalchemy.orm import Query

def encode_cursor(dt: datetime, record_id: str) -> str:
    """Encodes a datetime and record ID into a base64 string."""
    data = {
        "timestamp": dt.isoformat() if dt else None,
        "id": record_id
    }
    json_bytes = json.dumps(data).encode("utf-8")
    return base64.b64encode(json_bytes).decode("utf-8")

def decode_cursor(cursor_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """Decodes a base64 cursor string into a datetime and record ID."""
    try:
        json_bytes = base64.b64decode(cursor_str.encode("utf-8"))
        data = json.loads(json_bytes.decode("utf-8"))
        ts = data.get("timestamp")
        dt = datetime.fromisoformat(ts) if ts else None
        return dt, data.get("id")
    except Exception:
        return None, None

def paginate_query(
    query: Query,
    model_class: Any,
    limit: int = 20,
    cursor: Optional[str] = None
) -> Tuple[list, Optional[str]]:
    """
    Paginates a query using cursor-based pagination.
    Assumes descending order on updated_at and id.
    """
    if cursor:
        dt, record_id = decode_cursor(cursor)
        if dt:
            query = query.filter(
                (model_class.updated_at < dt) |
                ((model_class.updated_at == dt) & (model_class.id < record_id))
            )
            
    # Fetch limit + 1 to check if there is a next page
    results = query.order_by(model_class.updated_at.desc(), model_class.id.desc()).limit(limit + 1).all()
    
    has_next = len(results) > limit
    paginated_results = results[:limit]
    
    next_cursor = None
    if has_next and paginated_results:
        last_item = paginated_results[-1]
        next_cursor = encode_cursor(last_item.updated_at, last_item.id)
        
    return paginated_results, next_cursor
