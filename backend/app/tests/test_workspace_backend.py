import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.workspace_mode import WorkspaceMode
from app.services.workspace_service import workspace_service
from app.services.data_analysis_service import analyze_dataset, format_dataset_summary_for_llm
from app.services.workspace_prompts import get_workspace_prompt
from app.services.auth_service import hash_password, create_access_token

Base.metadata.create_all(bind=engine)
client = TestClient(app)

@pytest.fixture(scope="module")
def auth_context():
    """Create a test user and valid auth token for workspace testing."""
    session = SessionLocal()
    email = "workspace_test_user@nova-ai.local"
    session.query(User).filter(User.email == email).delete()
    session.commit()

    user = User(
        name="Workspace User",
        email=email,
        password_hash=hash_password("WorkspacePass123!")
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.id})
    cookies = {"access_token": token}
    headers = {"Authorization": f"Bearer {token}"}

    yield {"user": user, "token": token, "cookies": cookies, "headers": headers, "session": session}

    session.close()


# 1. Test Workspace Domain Model & Enums
def test_workspace_enum_normalization():
    assert WorkspaceMode.normalize("general") == WorkspaceMode.GENERAL
    assert WorkspaceMode.normalize("general ai") == WorkspaceMode.GENERAL
    assert WorkspaceMode.normalize("research") == WorkspaceMode.RESEARCH
    assert WorkspaceMode.normalize("deep_research") == WorkspaceMode.RESEARCH
    assert WorkspaceMode.normalize("writing") == WorkspaceMode.WRITING
    assert WorkspaceMode.normalize("coding") == WorkspaceMode.CODING
    assert WorkspaceMode.normalize("code") == WorkspaceMode.CODING
    assert WorkspaceMode.normalize("documents") == WorkspaceMode.DOCUMENTS
    assert WorkspaceMode.normalize("rag") == WorkspaceMode.DOCUMENTS
    assert WorkspaceMode.normalize("data-analysis") == WorkspaceMode.DATA_ANALYSIS
    assert WorkspaceMode.normalize("data_analysis") == WorkspaceMode.DATA_ANALYSIS
    assert WorkspaceMode.normalize("agent") == WorkspaceMode.AGENT
    assert WorkspaceMode.normalize("agent workspace") == WorkspaceMode.AGENT
    
    # Invalid mode returns None
    assert WorkspaceMode.normalize("invalid_mode_123") is None


# 2. Test System Prompts
def test_workspace_system_prompts():
    for mode in ["general", "research", "writing", "coding", "documents", "data-analysis", "agent"]:
        prompt = get_workspace_prompt(mode)
        assert prompt is not None
        assert len(prompt) > 20


# 3. Test Data Analysis Service on Real CSV
def test_data_analysis_service_calculation():
    csv_sample = (
        "name,age,salary,department\n"
        "Alice,30,70000,Engineering\n"
        "Bob,40,90000,Engineering\n"
        "Charlie,25,50000,Marketing\n"
        "David,,60000,Marketing\n"
    )
    result = analyze_dataset(csv_sample)
    assert result["row_count"] == 4
    assert result["column_count"] == 4

    # Check age column stats
    age_stat = next(c for c in result["columns"] if c["name"] == "age")
    assert age_stat["missing_count"] == 1
    assert age_stat["non_null_count"] == 3
    assert age_stat["min"] == 25.0
    assert age_stat["max"] == 40.0
    assert age_stat["mean"] == 31.6667
    assert age_stat["median"] == 30.0

    # Test summary formatting
    formatted = format_dataset_summary_for_llm(result)
    assert "DATASET STATISTICAL ANALYSIS" in formatted
    assert "Alice" in formatted


# 4. Test Workspace Metadata API Endpoints
def test_workspace_metadata_api(auth_context):
    res = client.get("/api/workspaces", cookies=auth_context["cookies"])
    assert res.status_code == 200
    raw_data = res.json()
    modes = raw_data.get("workspaces", raw_data) if isinstance(raw_data, dict) else raw_data
    assert len(modes) == 7
    ids = [m["id"] for m in modes]
    assert "general" in ids
    assert "research" in ids
    assert "writing" in ids
    assert "coding" in ids
    assert "documents" in ids
    assert "data-analysis" in ids
    assert "agent" in ids

def test_workspace_detail_api(auth_context):
    res = client.get("/api/workspaces/coding", cookies=auth_context["cookies"])
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "coding"
    assert data["name"] == "Coding"

def test_invalid_workspace_detail_api(auth_context):
    res = client.get("/api/workspaces/invalid_mode", cookies=auth_context["cookies"])
    assert res.status_code in (404, 422)


# 5. Test Invalid Workspace in Chat Request returns 400 or 422
def test_invalid_workspace_chat_request(auth_context):
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "workspace_mode": "bogus_workspace_99"
    }
    res = client.post("/api/chat/stream", json=payload, cookies=auth_context["cookies"])
    assert res.status_code in (400, 422)


# 6. Test Chat Request validation for empty messages
def test_empty_messages_chat_request(auth_context):
    payload = {
        "messages": [],
        "workspace_mode": "general"
    }
    res = client.post("/api/chat/stream", json=payload, cookies=auth_context["cookies"])
    assert res.status_code in (400, 422)


# 7. Test Chat Request for all 7 workspace modes
@pytest.mark.parametrize("mode", [
    "general",
    "research",
    "writing",
    "coding",
    "documents",
    "data-analysis",
    "agent"
])
def test_valid_workspace_chat_stream(auth_context, mode):
    payload = {
        "messages": [{"role": "user", "content": f"Test message for {mode} workspace"}],
        "workspace_mode": mode
    }
    with client.stream("POST", "/api/chat/stream", json=payload, cookies=auth_context["cookies"]) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")


# 8. Test Settings integration in both chat router endpoints
def test_workspace_chat_stream_with_settings(auth_context):
    payload = {
        "messages": [{"role": "user", "content": "Test message with custom settings"}],
        "workspace_mode": "general",
        "response_style": "concise",
        "response_tone": "technical",
        "semantic_chunk_limit": 3,
        "similarity_filtering": False
    }
    with client.stream("POST", "/api/chat/stream", json=payload, cookies=auth_context["cookies"]) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")

    # Test the workspaces endpoint /api/workspaces/{workspace_id}/chat as well
    payload_workspace = {
        "message": "Hello from workspace endpoint with custom settings",
        "response_style": "detailed",
        "response_tone": "friendly",
        "semantic_chunk_limit": 8,
        "similarity_filtering": True
    }
    with client.stream("POST", "/api/workspaces/general/chat", json=payload_workspace, cookies=auth_context["cookies"]) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")
