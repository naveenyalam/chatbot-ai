import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import app.models
from app.main import app
from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.core.rate_limit import _rate_limit_store

Base.metadata.create_all(bind=engine)
client = TestClient(app)

@pytest.fixture
def db_session():
    """Yield a database session for test execution."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clear overrides, cookies, and rate limits between tests."""
    app.dependency_overrides.clear()
    _rate_limit_store.clear()
    client.cookies.clear()
    yield
    app.dependency_overrides.clear()
    _rate_limit_store.clear()
    client.cookies.clear()

def test_user_registration_and_login_journey(db_session: Session):
    """Test the complete user onboarding loop: register user, login, retrieve me."""
    email = "phase17_journey@nova-ai.local"
    # Cleanup previous leftovers
    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()

    # 1. Register User
    reg_res = client.post(
        "/api/auth/register",
        json={"name": "Journey User", "email": email, "password": "Password123!"}
    )
    assert reg_res.status_code == 201
    assert "access_token" in reg_res.cookies

    # 2. Login User
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies

    # 3. Retrieve /me details
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == email

def test_chat_creation_and_session_journey(db_session: Session):
    """Test user chat workspace interaction."""
    email = "phase17_chat_journey@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Chat Journey User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    client.cookies.set("access_token", token)

    # 1. Create a Chat Session
    chat_res = client.post("/api/conversations", json={"title": "Journey Chat"})
    assert chat_res.status_code == 201
    chat_data = chat_res.json()
    assert chat_data["title"] == "Journey Chat"
    chat_id = chat_data["id"]

    # 2. List Chats
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    chats = list_res.json()
    assert any(c["id"] == chat_id for c in chats)

def test_session_expiry_trapping(db_session: Session):
    """Verify system throws 401 on expired or invalid token requests."""
    # Attempting request with expired/garbage token
    client.cookies.set("access_token", "expired_or_invalid_signature_token")
    
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "detail" in res.json()
