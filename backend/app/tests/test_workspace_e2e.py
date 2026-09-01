import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.workspaces.enums import WorkspaceMode
from app.workspaces.registry import workspace_registry
from app.services.auth_service import hash_password, create_access_token

Base.metadata.create_all(bind=engine)
client = TestClient(app)

@pytest.fixture(scope="module")
def e2e_auth():
    """Seed test user and create JWT token for workspace E2E testing."""
    session = SessionLocal()
    email = "workspace_e2e@nova-ai.local"
    session.query(User).filter(User.email == email).delete()
    session.commit()

    user = User(
        name="Workspace E2E User",
        email=email,
        password_hash=hash_password("E2EPass123!")
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.id})
    cookies = {"access_token": token}

    yield {"user": user, "token": token, "cookies": cookies, "session": session}

    session.close()


def test_e2e_workspace_list_and_detail(e2e_auth):
    # 1. Fetch workspaces list
    res = client.get("/api/workspaces", cookies=e2e_auth["cookies"])
    assert res.status_code == 200
    data = res.json()
    assert "workspaces" in data
    workspaces = data["workspaces"]
    assert len(workspaces) == 7

    mode_ids = [w["id"] for w in workspaces]
    for mode in ["general", "research", "writing", "coding", "documents", "data-analysis", "agent"]:
        assert mode in mode_ids

    # 2. Fetch detail for specific workspace
    res_detail = client.get("/api/workspaces/coding", cookies=e2e_auth["cookies"])
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == "coding"
    assert "code-generation" in detail["capabilities"]

    # 3. Fetch unknown workspace returns 404
    res_404 = client.get("/api/workspaces/unknown_mode_999", cookies=e2e_auth["cookies"])
    assert res_404.status_code == 404


def test_e2e_workspace_validation_endpoint(e2e_auth):
    res = client.post("/api/workspaces/documents/validate", json={"message": "Query docs"}, cookies=e2e_auth["cookies"])
    assert res.status_code == 200
    val = res.json()
    assert val["valid"] is True
    assert val["workspace_mode"] == "documents"


@pytest.mark.parametrize("mode", [
    "general",
    "research",
    "writing",
    "coding",
    "documents",
    "data-analysis",
    "agent"
])
def test_e2e_workspace_chat_flow(e2e_auth, mode):
    payload = {
        "message": f"Hello from {mode} workspace test",
        "messages": [{"role": "user", "content": f"Hello from {mode} workspace test"}]
    }

    with client.stream("POST", f"/api/workspaces/{mode}/chat", json=payload, cookies=e2e_auth["cookies"]) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                event_data = line[6:]
                if event_data != "[DONE]":
                    try:
                        events.append(json.loads(event_data))
                    except json.JSONDecodeError:
                        pass

        # Verify conversation ID event was emitted
        conv_event = next((e for e in events if e.get("type") == "conversation_id"), None)
        assert conv_event is not None
        conv_id = conv_event["value"]

        # Verify conversation in database retains active workspace mode
        db = e2e_auth["session"]
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        assert conv is not None
        assert conv.workspace_mode == WorkspaceMode.normalize(mode).value
