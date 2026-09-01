import pytest
import time
from fastapi.testclient import TestClient
import app.models
from app.main import app
from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token

Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def test_user_token():
    session = SessionLocal()
    email = "sse_perf@nova-ai.local"
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(name="SSE Perf User", email=email, password_hash=hash_password("Pass123!"))
        session.add(user)
        session.commit()
        session.refresh(user)
    token = create_access_token({"sub": user.id})
    session.close()
    return token

# 1. SSE Header Verification
def test_sse_performance_headers(test_user_token):
    payload = {"messages": [{"role": "user", "content": "Performance test"}], "stream": True, "mode": "chat"}
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": test_user_token}) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")
        assert "x-request-id" in res.headers

# 2. Time to First Token (TTFT) Benchmark
def test_sse_performance_ttft(test_user_token):
    payload = {"messages": [{"role": "user", "content": "TTFT test"}], "stream": True, "mode": "chat"}
    start_time = time.time()
    first_token_received = False
    ttft = None

    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": test_user_token}) as res:
        assert res.status_code == 200
        for line in res.iter_lines():
            if line and not first_token_received:
                ttft = time.time() - start_time
                first_token_received = True
                break

    assert first_token_received is True
    assert ttft is not None
    assert ttft < 10.0  # TTFT under 10 seconds for local mock provider simulation during test suite execution

# 3. Disconnect Stream Early Cancellation Handling
def test_sse_performance_disconnect_cancellation(test_user_token):
    payload = {"messages": [{"role": "user", "content": "Disconnect test"}], "stream": True, "mode": "chat"}
    lines_read = 0
    with client.stream("POST", "/api/chat/stream", json=payload, cookies={"access_token": test_user_token}) as res:
        assert res.status_code == 200
        for line in res.iter_lines():
            lines_read += 1
            if lines_read >= 2:
                break
    assert lines_read >= 2
