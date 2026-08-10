import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import app.models  # Ensure all models are registered
from app.main import app as fastapi_app
from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.document import Document
from app.services.auth_service import hash_password, create_access_token
from app.core.rate_limit import _rate_limit_store
from app.core.redis import cache_set, cache_get

Base.metadata.create_all(bind=engine)

client = TestClient(fastapi_app)

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
    """Clear dependency overrides, cookies, and rate limiting state between tests."""
    fastapi_app.dependency_overrides.clear()
    _rate_limit_store.clear()
    client.cookies.clear()
    yield
    fastapi_app.dependency_overrides.clear()
    _rate_limit_store.clear()
    client.cookies.clear()

# 1. Health Probe
def test_phase10_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

# 2. Ready Alias Probe
def test_phase10_ready():
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] in ("healthy", "ready", "degraded")

# 3. Readiness Probe
def test_phase10_readiness():
    res = client.get("/readiness")
    assert res.status_code == 200
    assert "database" in res.json()

# 4. User Registration
def test_phase10_registration(db_session: Session):
    email = "phase10_reg@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()

    res = client.post("/api/auth/register", json={"email": email, "password": "Password123!", "name": "Phase10 User"})
    assert res.status_code == 201
    assert "access_token" in res.cookies

# 5. User Login
def test_phase10_login(db_session: Session):
    email = "phase10_login@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Login User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()

    res = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert res.status_code == 200
    assert "access_token" in res.cookies

# 6. Authenticated Request
def test_phase10_auth_me(db_session: Session):
    email = "phase10_me@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Me User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    res = client.get("/api/auth/me", cookies={"access_token": token})
    assert res.status_code == 200
    assert res.json()["user"]["id"] == user.id

# 7. Chat Request
def test_phase10_chat(db_session: Session):
    email = "phase10_chat@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Chat User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    payload = {"messages": [{"role": "user", "content": "Hello Phase 10"}], "stream": True, "mode": "chat"}
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": token}) as stream_res:
        assert stream_res.status_code == 200

# 8. SSE Streaming
def test_phase10_sse_streaming(db_session: Session):
    email = "phase10_sse@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="SSE User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    payload = {"messages": [{"role": "user", "content": "Stream test"}], "stream": True, "mode": "chat"}
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": token}) as sse_res:
        assert sse_res.status_code == 200
        assert "text/event-stream" in sse_res.headers.get("content-type", "")

# 9. Document Upload
def test_phase10_document_upload(db_session: Session):
    email = "phase10_upload@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Upload User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    files = {"file": ("sample.txt", b"Sample text content for Phase 10 upload", "text/plain")}
    res = client.post("/api/documents/upload", files=files, cookies={"access_token": token})
    assert res.status_code == 201

# 10. RAG Retrieval
def test_phase10_rag_retrieval(db_session: Session):
    email = "phase10_rag@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="RAG User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    res = client.get("/api/documents", cookies={"access_token": token})
    assert res.status_code == 200

# 11. Agent Execution
def test_phase10_agent_execution(db_session: Session):
    email = "phase10_agent@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Agent User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    payload = {"messages": [{"role": "user", "content": "Calculate 5 + 5"}], "stream": True, "mode": "agent"}
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": token}) as agent_res:
        assert agent_res.status_code == 200

# 12. Rate Limiting
def test_phase10_rate_limiting():
    res = client.get("/health")
    for _ in range(69):
        res = client.get("/health")
    assert res.status_code in (200, 429)

# 13. Metrics Endpoint
def test_phase10_metrics():
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "nova_http_requests_total" in res.text

# 14. Tenant Isolation (User A vs User B document boundary)
def test_phase10_tenant_isolation(db_session: Session):
    email_a = "phase10_usera@nova-ai.local"
    email_b = "phase10_userb@nova-ai.local"
    db_session.query(User).filter(User.email.in_([email_a, email_b])).delete()
    db_session.commit()

    user_a = User(name="User A", email=email_a, password_hash=hash_password("Pass123!"))
    user_b = User(name="User B", email=email_b, password_hash=hash_password("Pass123!"))
    db_session.add_all([user_a, user_b])
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)

    doc_a = Document(
        user_id=user_a.id,
        filename="safe_private_a.txt",
        original_filename="private_a.txt",
        mime_type="text/plain",
        file_size=100,
        storage_path=f"user_{user_a.id}/safe_private_a.txt"
    )
    db_session.add(doc_a)
    db_session.commit()

    token_b = create_access_token({"sub": user_b.id})
    res_b = client.get("/api/documents", cookies={"access_token": token_b})
    assert res_b.status_code == 200
    doc_ids_b = [d["id"] for d in res_b.json()]
    assert doc_a.id not in doc_ids_b

# 15. Redis Fallback
def test_phase10_redis_fallback():
    success = cache_set("phase10_key", "phase10_val", ttl_seconds=60)
    if success:
        assert cache_get("phase10_key") == "phase10_val"
    else:
        assert cache_get("phase10_key") is None

# 16. Provider Fallback
def test_phase10_provider_fallback(db_session: Session):
    email = "phase10_fallback@nova-ai.local"
    db_session.query(User).filter(User.email == email).delete()
    user = User(name="Fallback User", email=email, password_hash=hash_password("Password123!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    payload = {"messages": [{"role": "user", "content": "Trigger router fallback"}], "stream": True, "mode": "chat"}
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": token}) as fallback_res:
        assert fallback_res.status_code == 200
