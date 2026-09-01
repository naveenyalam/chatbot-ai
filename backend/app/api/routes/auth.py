import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.schemas.user import UserResponse
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user
from app.core.rate_limit import RateLimiter
from app.core.config import settings

logger = logging.getLogger("nova-ai.routes.auth")
router = APIRouter()

# Auth rate limiter configured from environment
auth_limiter = RateLimiter(requests=settings.RATE_LIMIT_AUTH, window=60, key_prefix="auth")

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(auth_limiter)])
async def register(
    register_req: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == register_req.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    try:
        # Create and persist new user
        new_user = User(
            name=register_req.name,
            email=register_req.email,
            password_hash=hash_password(register_req.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Log action securely without exposing credentials
        logger.info(f"Successfully registered new user ID: {new_user.id}")

        # Auto-login: Issue JWT session token
        token = create_access_token(data={"sub": new_user.id})
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=3600 * 24, # 24 hours
            expires=3600 * 24,
            samesite="lax",
            secure=settings.SECURE_COOKIES,
        )

        return {"user": UserResponse.model_validate(new_user)}
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed user registration transaction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user. Please try again."
        )

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(auth_limiter)])
async def login(
    login_req: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    # Fetch user records
    user = db.query(User).filter(User.email == login_req.email).first()
    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Issue token and store in HttpOnly cookie
    token = create_access_token(data={"sub": user.id})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600 * 24,
        expires=3600 * 24,
        samesite="lax",
        secure=settings.SECURE_COOKIES,
    )

    logger.info(f"User {user.id} logged in successfully.")
    return {"user": UserResponse.model_validate(user)}

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """
    Clears the HttpOnly access token session cookie.
    """
    response.delete_cookie(
        key="access_token",
        samesite="lax",
        secure=settings.SECURE_COOKIES
    )
    logger.info(f"User {current_user.id} logged out successfully.")
    return {"detail": "Successfully logged out."}

@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns user profile parameters if active cookie is validated.
    """
    return {"user": UserResponse.model_validate(current_user)}
