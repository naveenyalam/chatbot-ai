import bcrypt
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

logger = logging.getLogger("nova-ai.auth-service")

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    """
    try:
        pwd_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception as exc:
        logger.error(f"Error verifying password hash: {exc}")
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generates a JWT access token containing subject claims.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Store expiration claim as timestamp
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT token. Returns payload or None if invalid.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token signature has expired.")
        return None
    except jwt.PyJWTError as exc:
        logger.warning(f"JWT token decoding failed: {exc}")
        return None

import time
_user_cache: dict[str, tuple[User, float]] = {}
_USER_CACHE_TTL_SECONDS = 60.0

def invalidate_user_cache(user_id: str):
    """Invalidates cached user state when account properties are mutated."""
    _user_cache.pop(user_id, None)

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the user context from request cookies or Authorization headers.
    Uses sub-millisecond in-memory TTL caching to avoid redundant DB roundtrips.
    """
    # 1. Read token from cookie
    token = request.cookies.get("access_token")
    
    # 2. Fallback to Bearer token in Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing."
        )

    # 3. Decode token payload
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid."
        )

    user_id = payload["sub"]
    now = time.time()
    if user_id in _user_cache:
        cached_user, cached_at = _user_cache[user_id]
        if now - cached_at < _USER_CACHE_TTL_SECONDS:
            try:
                return db.merge(cached_user, load=False)
            except Exception:
                _user_cache.pop(user_id, None)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    _user_cache[user_id] = (user, now)
    return user
