import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.document import Document
from app.services.document.pdf import PDFExtractor
from app.services.document.csv import CSVExtractor
from app.services.document.txt import TxtExtractor

# Use the dedicated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nova.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup schemas
Base.metadata.create_all(bind=engine)

# Seed Users
db = TestingSessionLocal()
user_a = db.query(User).filter(User.email == "usera@example.com").first()
if not user_a:
    user_a = User(id="user-a-id", name="User A", email="usera@example.com", password_hash="hash")
    db.add(user_a)
user_b = db.query(User).filter(User.email == "userb@example.com").first()
if not user_b:
    user_b = User(id="user-b-id", name="User B", email="userb@example.com", password_hash="hash")
    db.add(user_b)
db.commit()
db.close()

from fastapi import Depends

active_user_email = "usera@example.com"

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

async def override_get_current_user(db = Depends(get_db)):
    user = db.query(User).filter(User.email == active_user_email).first()
    return user

@pytest.fixture(autouse=True)
def setup_rag_overrides():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


def test_unsupported_file_type():
    global active_user_email
    active_user_email = "usera@example.com"
    
    # .exe is not a supported type; images and documents are
    file_payload = {"file": ("test.exe", b"MZ\x90\x00", "application/octet-stream")}
    response = client.post("/api/documents/upload", files=file_payload)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_txt_document():
    global active_user_email
    active_user_email = "usera@example.com"

    file_payload = {"file": ("test.txt", b"Hello from Nova AI document context test.", "text/plain")}
    response = client.post("/api/documents/upload", files=file_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test.txt"
    assert data["status"] == "uploaded"
    
    doc_id = data["id"]
    
    # Check status endpoint
    status_response = client.get(f"/api/documents/{doc_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["id"] == doc_id
    
    # Clean up
    delete_response = client.delete(f"/api/documents/{doc_id}")
    assert delete_response.status_code == 200


def test_user_document_isolation():
    global active_user_email
    # 1. User A uploads a document
    active_user_email = "usera@example.com"
    file_payload = {"file": ("private.txt", b"Secret credentials data.", "text/plain")}
    res_upload = client.post("/api/documents/upload", files=file_payload)
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["id"]

    # 2. Switch context to User B and check access to User A's document
    active_user_email = "userb@example.com"
    res_get = client.get(f"/api/documents/{doc_id}")
    assert res_get.status_code == 404  # Unauthorized yields safe 404

    res_delete = client.delete(f"/api/documents/{doc_id}")
    assert res_delete.status_code == 404

    # 3. Clean up using User A
    active_user_email = "usera@example.com"
    res_cleanup = client.delete(f"/api/documents/{doc_id}")
    assert res_cleanup.status_code == 200



def test_extractors():
    # Test CSV extractor
    csv_data = b"Name,Age,Role\nAlice,30,Engineer\nBob,25,Designer"
    # Write to a temp file
    temp_csv_path = "temp_test_file.csv"
    with open(temp_csv_path, "wb") as f:
        f.write(csv_data)
        
    try:
        extractor = CSVExtractor()
        res = extractor.extract(temp_csv_path)
        assert "Alice" in res["text"]
        assert "Age" in res["text"]
        assert "Designer" in res["text"]
        assert res["metadata"]["row_count"] == 2
    finally:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

    # Test TXT extractor
    temp_txt_path = "temp_test_file.txt"
    with open(temp_txt_path, "w", encoding="utf-8") as f:
        f.write("Hello Text")
    try:
        extractor = TxtExtractor()
        res = extractor.extract(temp_txt_path)
        assert res["text"] == "Hello Text"
    finally:
        if os.path.exists(temp_txt_path):
            os.remove(temp_txt_path)
