# pyrefly: ignore [missing-import]
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.services.auth_service import get_current_user
from app.models.user import User

# Setup dedicated SQLite test database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nova.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Re-create database schema tables for clean testing
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Seed mock test user
db = TestingSessionLocal()
mock_db_user = User(
    id="test-user-uuid",
    name="Test User",
    email="test@example.com",
    password_hash="fakehash"
)
db.add(mock_db_user)
db.commit()
db.refresh(mock_db_user)
db.close()

from fastapi import Depends

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def override_get_current_user(db = Depends(get_db)):
    user = db.query(User).filter(User.id == "test-user-uuid").first()
    return user

# Register overrides globally on the app container
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(autouse=True, scope="module")
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


def test_health_endpoint():
    """
    Verifies that the /health diagnostic page responds correctly.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nova-ai-backend"
    assert "ai_provider" in data

def test_api_health_endpoint():
    """
    Verifies that the /api/health diagnostic page responds correctly.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nova-ai-backend"
    assert "ai_provider" in data

def test_empty_messages_validation():
    """
    Verifies that empty messages arrays are caught and rejected.
    """
    response = client.post("/api/chat/stream", json={
        "messages": [],
        "model": "nova-intelligence"
    })
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"

def test_invalid_temperature_validation():
    """
    Verifies that out-of-bounds temperature values are rejected.
    """
    response = client.post("/api/chat/stream", json={
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 2.5
    })
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"

def test_invalid_role_validation():
    """
    Verifies that invalid message roles are rejected.
    """
    response = client.post("/api/chat/stream", json={
        "messages": [{"role": "invalid_role", "content": "hi"}]
      })
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"

def test_message_too_long_validation():
    """
    Verifies that excessively long user prompts are caught.
    """
    long_prompt = "x" * 60001
    response = client.post("/api/chat/stream", json={
        "messages": [{"role": "user", "content": long_prompt}]
    })
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"

def test_streaming_response_transmission():
    """
    Verifies that the streaming endpoint yields chunks correctly.
    """
    import json
    response = client.post("/api/chat/stream", json={
        "messages": [{"role": "user", "content": "ping"}],
        "model": "nova-fast"
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    chunks = []
    for line in response.iter_lines():
        line_clean = line.strip()
        if line_clean.startswith("data: "):
            chunks.append(line_clean[6:])

    assert len(chunks) > 0

    conversation_id_found = False
    for c in chunks:
        if c == "[DONE]":
            continue
        try:
            data = json.loads(c)
            if data.get("type") == "conversation_id":
                conversation_id_found = True
        except json.JSONDecodeError:
            pass

    assert conversation_id_found
    assert "[DONE]" in chunks

def test_readiness_endpoint():
    """
    Verifies that the /readiness endpoint returns 200/503 according to dependencies.
    """
    # In development/test mode without REDIS_URL, it should return 200 with local-fallback
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "ok"
    assert response.json()["redis"] == "local-fallback"

def test_request_id_generation_and_propagation():
    """
    Verifies that FastAPI generates a request ID, responds with it in headers,
    and propagates it correctly.
    """
    # 1. Test generated request ID
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("nova-")

    # 2. Test client-supplied request ID propagation
    custom_id = "test-request-id-1234"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id

def test_metrics_endpoint():
    """
    Verifies that the /metrics endpoint returns standard Prometheus text.
    """
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "nova_http_requests_total" in response.text or "process_cpu_seconds_total" in response.text

def test_structured_error_responses_with_request_id():
    """
    Verifies that structured error responses contain the request_id.
    """
    response = client.post("/api/chat/stream", json={})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "request_id" in data["error"]
    assert data["error"]["code"] == "INVALID_REQUEST"

def test_metrics_recording_on_request():
    """
    Verifies that requests increment the Prometheus counter.
    """
    from prometheus_client import REGISTRY
    
    labels = {'method': 'GET', 'endpoint': '/health', 'status_code': '200'}
    before = REGISTRY.get_sample_value('nova_http_requests_total', labels)
    if before is None:
        before = REGISTRY.get_sample_value('nova_http_requests_total_total', labels) or 0.0
        
    client.get("/health")
    
    after = REGISTRY.get_sample_value('nova_http_requests_total', labels)
    if after is None:
        after = REGISTRY.get_sample_value('nova_http_requests_total_total', labels) or 0.0
        
    assert after >= before + 1.0


