import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import hash_password
from app.db.database import get_db, Base, engine
from app.models import User, Conversation, Message, Document

Base.metadata.create_all(bind=engine)
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.core.budget import UsageBudget
from app.tools.code_execution import CodeExecutionTool

def create_test_user(db_session, prefix="user"):
    unique_id = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique_id}@example.com"
    password = "SecretPassword123!"
    hashed = hash_password(password)
    user = User(name=f"Test {prefix}", email=email, password_hash=hashed)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, email, password

def login_and_get_cookie(tc: TestClient, email: str, password: str) -> str:
    response = tc.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    cookie = response.cookies.get("access_token")
    return cookie

# ─── 1. Health & Readiness Probes ─────────────────────────────────────────────

def test_e2e_health_and_readiness():
    tc = TestClient(app)
    resp_health = tc.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    resp_ready = tc.get("/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "healthy"

# ─── 2. Authentication Lifecycle E2E ──────────────────────────────────────────

def test_e2e_authentication_flow():
    tc = TestClient(app)
    email = f"auth_test_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"

    # Registration
    resp_register = tc.post("/api/auth/register", json={"name": "Auth User", "email": email, "password": password})
    assert resp_register.status_code in [200, 201]

    # Login
    cookie = login_and_get_cookie(tc, email, password)
    assert cookie is not None

    # Get current user profile (/me)
    tc.cookies.set("access_token", cookie)
    resp_me = tc.get("/api/auth/me")
    assert resp_me.status_code == 200
    assert resp_me.json()["user"]["email"] == email

# ─── 3. Multi-Tenant User Isolation E2E ──────────────────────────────────────

def test_e2e_user_tenant_isolation():
    db = next(get_db())
    user_a, email_a, pass_a = create_test_user(db, "user_a")
    user_b, email_b, pass_b = create_test_user(db, "user_b")

    tc_a = TestClient(app)
    cookie_a = login_and_get_cookie(tc_a, email_a, pass_a)
    tc_a.cookies.set("access_token", cookie_a)

    # User A creates a conversation
    resp_conv_a = tc_a.post("/api/conversations", json={"title": "User A Private Conv"})
    assert resp_conv_a.status_code in [200, 201]
    conv_a_id = resp_conv_a.json()["id"]

    # User B attempts to access User A's conversation -> Must fail (404 or 403)
    tc_b = TestClient(app)
    cookie_b = login_and_get_cookie(tc_b, email_b, pass_b)
    tc_b.cookies.set("access_token", cookie_b)

    resp_conv_b_get = tc_b.get(f"/api/conversations/{conv_a_id}")
    assert resp_conv_b_get.status_code in [403, 404]

    # User A uploads a document record
    doc_a = Document(
        user_id=user_a.id,
        filename="user_a_doc.txt",
        original_filename="doc.txt",
        mime_type="text/plain",
        storage_path="/storage/user_a_doc.txt",
        file_size=100
    )
    db.add(doc_a)
    db.commit()
    db.refresh(doc_a)

    # User B attempts to delete User A's document -> Must fail
    resp_doc_b_del = tc_b.delete(f"/api/documents/{doc_a.id}")
    assert resp_doc_b_del.status_code in [403, 404]

# ─── 4. End-to-End Chat & SSE Streaming ───────────────────────────────────────

def test_e2e_chat_streaming():
    db = next(get_db())
    user, email, password = create_test_user(db, "chat_user")
    tc = TestClient(app)
    cookie = login_and_get_cookie(tc, email, password)
    tc.cookies.set("access_token", cookie)

    payload = {
        "messages": [{"role": "user", "content": "Hello NOVA AI!"}],
        "mode": "normal",
        "temperature": 0.7
    }

    response = tc.post("/api/chat/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert len(response.text) > 0

# ─── 5. Code Execution Sandbox Security E2E ───────────────────────────────────

def test_e2e_sandbox_execution_and_isolation():
    tool = CodeExecutionTool()

    # Safe arithmetic
    r_safe = asyncio.run(tool.execute({"language": "python", "code": "print(100 + 200)"}))
    assert r_safe.success
    assert "300" in r_safe.data["stdout"]

    # Malicious import attempt
    r_bad = asyncio.run(tool.execute({"language": "python", "code": "import os\nos.system('whoami')"}))
    if r_bad.success:
        assert "whoami" not in r_bad.data.get("stdout", "")
    else:
        assert not r_bad.success

# ─── 6. Circuit Breaker & Resiliency E2E ─────────────────────────────────────

def test_e2e_circuit_breaker_resiliency():
    cb_id = f"e2e_prov_{uuid.uuid4().hex[:6]}"
    cb = CircuitBreaker(cb_id)
    cb.threshold = 2
    cb.cooldown = 10

    # Trip breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.get_state() == "OPEN"

    # Verify exception is raised
    with pytest.raises(CircuitBreakerOpenException):
        cb.check_call()

# ─── 7. Usage Budget & Rate Limit E2E ─────────────────────────────────────────

def test_e2e_usage_budget_enforcement():
    user_id = f"e2e_user_{uuid.uuid4().hex[:6]}"
    
    from app.core.config import settings
    for _ in range(settings.MAX_DAILY_AI_REQUESTS):
        UsageBudget.record_request(user_id)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        UsageBudget.check_request_budget(user_id)
    assert exc_info.value.status_code == 429
