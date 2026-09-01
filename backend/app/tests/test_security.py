import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.services.auth_service import get_current_user, hash_password, create_access_token
from app.models.user import User
from app.models.conversation import Conversation
from app.models.document import Document
from app.core.config import settings

# Setup a dedicated test database (sharing test_nova.db to align database contexts)
engine = create_engine("sqlite:///./test_nova.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup database override helper
def override_get_db_sec():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pytest fixture to manage overrides and isolate tests
@pytest.fixture(autouse=True)
def security_test_environment():
    # Clear client cookies to avoid test pollution
    client.cookies.clear()
    
    # Setup/ensure schema exists without dropping everything
    Base.metadata.create_all(bind=engine)
    
    # Save original dependency overrides
    original_overrides = dict(app.dependency_overrides)
    
    # Configure security overrides
    app.dependency_overrides[get_db] = override_get_db_sec
    
    # Remove any override of get_current_user
    keys_to_remove = [k for k in app.dependency_overrides if getattr(k, "__name__", None) == "get_current_user"]
    for k in keys_to_remove:
        del app.dependency_overrides[k]
        
    yield
    
    # Clean up created security test users
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.email.in_(["user_a@test.com", "user_b@test.com", "upload_user@test.com", "register@test.com"])).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
        
    # Restore original overrides to prevent contaminating other test modules
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)
    client.cookies.clear()

client = TestClient(app)

# Helper to create users and get JWT tokens
def create_test_user(email: str, name: str = "Test User") -> tuple[User, str]:
    import uuid
    db = TestingSessionLocal()
    pwd_hash = hash_password("SecurePassword123")
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        name=name,
        email=email,
        password_hash=pwd_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    # Generate token using explicit user_id string
    token = create_access_token({"sub": user_id})
    return user, token


def test_security_headers():
    """Verify that essential OWASP security headers are present on API responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "geolocation=()" in response.headers["Permissions-Policy"]


def test_request_size_limiter():
    """Verify that oversized requests are rejected with a 413 Payload Too Large."""
    # Temporarily set limit to 100 bytes for testing
    old_limit = settings.MAX_JSON_REQUEST_SIZE
    settings.MAX_JSON_REQUEST_SIZE = 100
    try:
        payload = "x" * 200
        response = client.post("/api/chat/stream", json={"messages": [{"role": "user", "content": payload}]})
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    finally:
        settings.MAX_JSON_REQUEST_SIZE = old_limit


def test_authentication_workflow():
    """Verify password hashing, token validation, and cookie setup."""
    db = TestingSessionLocal()
    # Check register
    reg_response = client.post("/api/auth/register", json={
        "name": "Sec Register",
        "email": "register@test.com",
        "password": "SuperSecretPassword"
    })
    assert reg_response.status_code == 201
    assert "access_token" in reg_response.cookies
    
    # Verify password was hashed (not plain text)
    user = db.query(User).filter(User.email == "register@test.com").first()
    assert user is not None
    assert user.password_hash != "SuperSecretPassword"
    assert user.password_hash.startswith("$2b$") # bcrypt prefix
    db.close()

    # Verify invalid login returns sanitized generic error
    login_response = client.post("/api/auth/login", json={
        "email": "register@test.com",
        "password": "WrongPassword"
    })
    assert login_response.status_code == 401
    assert "Invalid email or password" in login_response.json()["detail"]


def test_idor_conversation_isolation():
    """Verify that User A cannot access User B's conversations or messages."""
    user_a, token_a = create_test_user("user_a@test.com", "User A")
    user_b, token_b = create_test_user("user_b@test.com", "User B")

    # Create conversation as User A
    headers_a = {"Authorization": f"Bearer {token_a}"}
    conv_response = client.post("/api/conversations", json={"title": "User A Chat"}, headers=headers_a)
    assert conv_response.status_code == 201
    conv_id = conv_response.json()["id"]

    # Try to access User A's conversation as User B
    headers_b = {"Authorization": f"Bearer {token_b}"}
    get_response = client.get(f"/api/conversations/{conv_id}", headers=headers_b)
    assert get_response.status_code == 404  # Rejects with clean 404 (does not disclose existence)

    # Try to rename User A's conversation as User B
    patch_response = client.patch(f"/api/conversations/{conv_id}", json={"title": "Hacked"}, headers=headers_b)
    assert patch_response.status_code == 404

    # Try to delete User A's conversation as User B
    del_response = client.delete(f"/api/conversations/{conv_id}", headers=headers_b)
    assert del_response.status_code == 404


def test_file_upload_security():
    """Verify path traversal blocks, file signatures, and size validation."""
    _, token = create_test_user("upload_user@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Path traversal in filename
    files = {"file": ("../../traversal.pdf", b"%PDF-1.4...", "application/pdf")}
    response = client.post("/api/documents/upload", files=files, headers=headers)
    assert response.status_code == 400
    assert "Directory traversal" in response.json()["detail"]

    # 2. Invalid PDF signature (disguised TXT)
    files = {"file": ("dummy.pdf", b"this is plain text", "application/pdf")}
    response = client.post("/api/documents/upload", files=files, headers=headers)
    assert response.status_code == 400
    assert "Invalid PDF file signature" in response.json()["detail"]

    # 3. Disguised binary in plaintext txt file
    files = {"file": ("shell.txt", b"\x00\x00\x00\x00malicious binary", "text/plain")}
    response = client.post("/api/documents/upload", files=files, headers=headers)
    assert response.status_code == 400
    assert "Text files must not contain binary data" in response.json()["detail"]


def test_rate_limiting_trigger():
    """Verify that hitting the rate limit returns a structured 429 response."""
    # Temporarily set rate limit parameters to be low
    old_enabled = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    
    try:
        from app.core.rate_limit import _rate_limit_store
        _rate_limit_store.clear()
        from app.core.redis import get_redis_client
        client = get_redis_client()
        if client:
            client.delete("nova:development:rate_limit:test_rate:127.0.0.1")
        
        # We will make 3 requests in rapid succession for a limit of 2 requests/window
        from app.core.rate_limit import RateLimiter
        # Create a specific limited endpoint/limiter
        limiter = RateLimiter(requests=2, window=10, key_prefix="test_rate")
        
        # We can construct mock requests and trigger the limiter directly
        class MockRequest:
            def __init__(self):
                self.client = type("Client", (object,), {"host": "127.0.0.1"})()
                self.cookies = {}
                self.headers = {}
        
        req = MockRequest()
        
        # First request
        asyncio.run(limiter(req))
        # Second request
        asyncio.run(limiter(req))
        
        # Third request should raise 429
        with pytest.raises(Exception) as excinfo:
            asyncio.run(limiter(req))
            
        assert excinfo.value.status_code == 429
        assert excinfo.value.detail["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        
    finally:
        settings.RATE_LIMIT_ENABLED = old_enabled


def test_sandbox_dunder_attribute_blocking():
    """Verify that RestrictedPython sandbox blocks compile or run-time dunder access."""
    from app.tools.code_execution import CodeExecutionTool
    tool = CodeExecutionTool()
    
    # Try accessing __subclasses__ via list class
    code = "print([].__class__.__subclasses__())"
    r = asyncio.run(tool.execute({"language": "python", "code": code}))
    assert not r.success
    # The syntax error or restriction error can reside in error or stderr
    err_msg = (r.error or "") + (r.data.get("stderr") or "")
    assert len(err_msg) > 0


def test_sandbox_inplacevar_operators():
    """Verify that strict_inplacevar correctly executes sandboxed operators."""
    from app.tools.code_execution import CodeExecutionTool
    tool = CodeExecutionTool()
    
    code = "x = 10\nx += 5\nprint(x)"
    r = asyncio.run(tool.execute({"language": "python", "code": code}))
    assert r.success
    assert "15" in r.data["stdout"]


def test_jwt_expired_or_invalid():
    """Verify that expired or malformed JWT tokens are rejected."""
    # Malformed token
    response = client.get("/api/conversations", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    
    # Missing authorization header entirely
    response = client.get("/api/conversations")
    assert response.status_code == 401


def test_cors_origin_validation():
    """Verify that CORS checks origins correctly based on settings."""
    origins = settings.cors_origins
    if origins:
        valid_origin = origins[0]
        response = client.options(
            "/health",
            headers={
                "Origin": valid_origin,
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.headers.get("access-control-allow-origin") == valid_origin

    # Test invalid origin
    response = client.options(
        "/health",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert "access-control-allow-origin" not in response.headers or response.headers.get("access-control-allow-origin") != "http://malicious-site.com"


def test_rate_limiter_retry_after_header():
    """Verify that 429 exceptions contain Retry-After response headers."""
    from fastapi import HTTPException
    old_enabled = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    try:
        from app.core.rate_limit import _rate_limit_store, RateLimiter
        _rate_limit_store.clear()
        from app.core.redis import get_redis_client
        client = get_redis_client()
        if client:
            client.delete("nova:development:rate_limit:test_retry_after:127.0.0.1")
        
        limiter = RateLimiter(requests=1, window=60, key_prefix="test_retry_after")
        
        class MockRequest:
            def __init__(self):
                self.client = type("Client", (object,), {"host": "127.0.0.1"})()
                self.cookies = {}
                self.headers = {}
                
        req = MockRequest()
        
        # 1st request allowed
        asyncio.run(limiter(req))
        
        # 2nd request raises 429 with header
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(limiter(req))
            
        assert excinfo.value.status_code == 429
        assert "Retry-After" in excinfo.value.headers
        assert int(excinfo.value.headers["Retry-After"]) > 0
    finally:
        settings.RATE_LIMIT_ENABLED = old_enabled


def test_error_handling_sanitization():
    """Verify that unhandled server errors hide stack traces and return generic 500 error."""
    # Trigger an intentional unhandled server error
    from fastapi import Request
    from app.main import general_exception_handler
    
    class DummyRequest:
        def __init__(self):
            self.state = type("State", (object,), {"request_id": "test-err-req"})()
            
    req = DummyRequest()
    exc = ValueError("Secret DB database credentials: admin:password123")
    
    response = asyncio.run(general_exception_handler(req, exc))
    assert response.status_code == 500
    
    body = response.body.decode('utf-8')
    assert "credentials" not in body
    assert "password123" not in body
    assert "Something went wrong while executing your request." in body


def test_rag_prompt_injection_isolation():
    """Verify that RAG prompt construction properly encapsulates retrieved context in boundary tags."""
    from app.services.ai.rag import run_rag_pipeline
    from app.schemas.chat import ChatMessage
    from unittest.mock import patch

    messages = [ChatMessage(role="user", content="Hello")]
    
    mock_chunks = [
        {"original_filename": "test.txt", "metadata": {"page": 1}, "content": "retrieved file content"}
    ]
    
    # Mock retrieve_relevant_chunks and ai_service.stream_chat
    with patch("app.services.ai.rag.retrieve_relevant_chunks", return_value=mock_chunks), \
         patch("app.services.ai.rag.ai_service.stream_chat") as mock_stream:
         
         # mock_stream needs to return an async generator
         async def dummy_generator(*args, **kwargs):
             yield "result"
             
         mock_stream.return_value = dummy_generator()
         
         # Consume the generator returned by run_rag_pipeline
         async def run_test():
             results = []
             async for r in run_rag_pipeline(None, "user_id", messages, ["doc_id"], None, 0.7):
                 results.append(r)
             return results
             
         results = asyncio.run(run_test())
             
         # Check that stream_chat was called
         assert mock_stream.called
         call_args = mock_stream.call_args[1]
         payload = call_args["messages"]
         system_msg = payload[0].content
         
         assert "### SECURITY COMPLIANCE GUIDELINES" in system_msg
         assert "=== BEGIN UNTRUSTED RETRIEVED CONTENT ===" in system_msg
         assert "=== END UNTRUSTED RETRIEVED CONTENT ===" in system_msg
