import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
import app.models
from app.main import app
from app.db.database import get_db, SessionLocal, Base, engine
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token, get_current_user
from app.api.routes.auth import auth_limiter
from app.core.rate_limit import _rate_limit_store

Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def db_session():
    """Yield a database session for test teardown."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Ensure dependency overrides and rate limits are cleared around tests."""
    app.dependency_overrides.clear()
    _rate_limit_store.clear()
    yield
    app.dependency_overrides.clear()
    _rate_limit_store.clear()

def test_smoke_health_and_liveness():
    """Verify backend process liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nova-ai-backend"

def test_smoke_readiness_probe():
    """Verify backend dependency-aware readiness probe."""
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ready", "degraded")
    assert "database" in data
    assert "redis" in data

def test_smoke_ready_alias_probe():
    """Verify standard Kubernetes /ready alias probe."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ready", "degraded")

def test_smoke_auth_workflow_and_cookies(db_session: Session):
    """Verify user registration, login, JWT token issuance, and HttpOnly cookies."""
    email = "smoke_user_test@nova-ai.local"
    password = "SmokePassword123!"

    # Clean up existing test user if present
    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()

    # 1. Register new user
    reg_payload = {"email": email, "password": password, "name": "Smoke User"}
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert "access_token" in reg_res.cookies
    user_id = reg_res.json()["user"]["id"]

    # 2. Login with credentials
    login_payload = {"email": email, "password": password}
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies

    # 3. Access protected route with session cookie
    client.cookies.set("access_token", login_res.cookies["access_token"])
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["user"]["id"] == user_id
    client.cookies.clear()

def test_smoke_unauthenticated_protected_route_rejection():
    """Verify unauthenticated requests to protected endpoints return 401 Unauthorized."""
    app.dependency_overrides.pop(get_current_user, None)
    client.cookies.clear()
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_smoke_cors_headers():
    """Verify CORS preflight response headers."""
    response = client.options(
        "/api/chat/stream",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_smoke_prometheus_metrics_and_label_safety():
    """Verify /metrics endpoint output and absence of sensitive high-cardinality labels."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "nova_http_requests_total" in content
    assert "smoke_user_test@nova-ai.local" not in content
    assert "SmokePassword123!" not in content

def test_smoke_redis_cache_fallback():
    """Verify Redis caching and fallback behavior."""
    from app.core.redis import cache_set, cache_get
    success = cache_set("smoke_test_key", "smoke_val", ttl_seconds=60)
    if success:
        assert cache_get("smoke_test_key") == "smoke_val"
    else:
        assert cache_get("smoke_test_key") is None

def test_smoke_database_direct_connectivity(db_session: Session):
    """Verify active SQL database connection execution."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_smoke_sse_streaming_headers(db_session: Session):
    """Verify SSE streaming route returns proper event stream headers."""
    email = "sse_user_test@nova-ai.local"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name="SSE Smoke User",
            email=email,
            password_hash=hash_password("Pass123!")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    token = create_access_token(data={"sub": user.id})

    chat_payload = {
        "messages": [{"role": "user", "content": "Hello Smoke Test"}],
        "stream": True,
        "mode": "chat"
    }

    client.cookies.set("access_token", token)
    with client.stream("POST", "/api/chat/stream", json=chat_payload) as stream_res:
        assert stream_res.status_code == 200
        assert "text/event-stream" in stream_res.headers.get("content-type", "")
    client.cookies.clear()
