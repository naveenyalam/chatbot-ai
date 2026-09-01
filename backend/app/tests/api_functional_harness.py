import httpx
import asyncio
import json
import uuid

BASE_URL = "http://localhost:8000"

async def run_harness():
    print("==============================================")
    print("NOVA AI — Phase 25 API Functional Test Harness")
    print("==============================================")

    # 1. System Health Checks
    print("\n--- 1. Diagnostic Endpoints ---")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        print(f"GET /health: {r.status_code} -> {r.json().get('status')}")
        
        r = await client.get(f"{BASE_URL}/api/health")
        print(f"GET /api/health: {r.status_code} -> {r.json().get('status')}")
        
        r = await client.get(f"{BASE_URL}/api/provider-status")
        print(f"GET /api/provider-status: {r.status_code} -> {r.json().get('configured')}")
        
        r = await client.get(f"{BASE_URL}/readiness")
        print(f"GET /readiness: {r.status_code}")

    # Generate unique emails
    test_uid = str(uuid.uuid4())[:8]
    email_a = f"usera_{test_uid}@nova.ai"
    email_b = f"userb_{test_uid}@nova.ai"
    password = "StrongPassword123"

    client_a = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
    client_b = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)

    # 2. Auth Endpoint Testing
    print("\n--- 2. Auth Endpoints ---")
    
    # Valid register User A
    r = await client_a.post("/api/auth/register", json={"email": email_a, "password": password, "name": "User A"})
    print(f"POST /api/auth/register (User A): {r.status_code}")

    # Duplicate register block check
    r = await client_b.post("/api/auth/register", json={"email": email_a, "password": password, "name": "User A"})
    print(f"POST /api/auth/register (Duplicate): {r.status_code} (Expected 400)")

    # Missing field register check
    r = await client_b.post("/api/auth/register", json={"email": "bad_email", "name": "User B"})
    print(f"POST /api/auth/register (Missing fields): {r.status_code} (Expected 422)")

    # Login User A with invalid password
    r = await client_a.post("/api/auth/login", json={"email": email_a, "password": "WrongPassword"})
    print(f"POST /api/auth/login (Invalid Password): {r.status_code} (Expected 401)")

    # Login User A successfully
    r = await client_a.post("/api/auth/login", json={"email": email_a, "password": password})
    print(f"POST /api/auth/login (User A Success): {r.status_code}")

    # Check /me profile
    r = await client_a.get("/api/auth/me")
    print(f"GET /api/auth/me (User A Profile): {r.status_code} -> email: {r.json().get('user', {}).get('email')}")

    # Access /me unauthorized
    anon_client = httpx.AsyncClient(base_url=BASE_URL)
    r = await anon_client.get("/api/auth/me")
    print(f"GET /api/auth/me (Unauthorized): {r.status_code} (Expected 401)")
    await anon_client.aclose()

    # Login User B successfully
    await client_b.post("/api/auth/register", json={"email": email_b, "password": password, "name": "User B"})
    r = await client_b.post("/api/auth/login", json={"email": email_b, "password": password})
    print(f"POST /api/auth/login (User B Success): {r.status_code}")

    # 3. Conversations Endpoint Testing
    print("\n--- 3. Conversations Endpoints ---")
    
    # Create conversation User A
    r = await client_a.post("/api/conversations", json={"title": "User A Topic"})
    conv_a = r.json()
    conv_a_id = conv_a.get("id")
    print(f"POST /api/conversations (User A): {r.status_code} -> ID: {conv_a_id}")

    # List conversations User A
    r = await client_a.get("/api/conversations")
    print(f"GET /api/conversations (User A): {r.status_code} -> Count: {len(r.json())}")

    # User B attempting to access User A's private conversation
    r = await client_b.get(f"/api/conversations/{conv_a_id}")
    print(f"GET /api/conversations/{{id}} (Cross-User Isolation): {r.status_code} (Expected 404/403)")

    # Retrieve non-existent conversation
    r = await client_a.get(f"/api/conversations/{uuid.uuid4()}")
    print(f"GET /api/conversations/{{id}} (Non-existent): {r.status_code} (Expected 404)")

    # 4. Chat Streaming Endpoint Testing
    print("\n--- 4. Chat Streaming Endpoints ---")
    
    # Valid Chat Stream
    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "conversation_id": conv_a_id,
        "model": "nova-intelligence",
        "temperature": 0.7
    }
    async with client_a.stream("POST", "/api/chat/stream", json=payload) as response:
        print(f"POST /api/chat/stream (Valid): {response.status_code}")
        first_line = ""
        async for line in response.aiter_lines():
            if line:
                first_line = line
                break
        print(f"  First Event Stream Chunk: {first_line[:120]}")

    # Malformed messages list payload
    bad_payload = {
        "messages": [],
        "conversation_id": conv_a_id
    }
    r = await client_a.post("/api/chat/stream", json=bad_payload)
    print(f"POST /api/chat/stream (Empty messages list): {r.status_code} (Expected 422/400)")

    # 5. Documents & RAG Endpoint Testing
    print("\n--- 5. Documents & RAG Endpoints ---")
    
    # Upload empty file
    files = {"file": ("empty.txt", b"", "text/plain")}
    r = await client_a.post("/api/documents/upload", files=files)
    print(f"POST /api/documents/upload (Empty File): {r.status_code} (Expected 400)")

    # Upload valid text document
    doc_text = "Standard Operating Procedure: Use port 8000 for FastAPI. Use port 3000 for Next.js."
    files = {"file": ("sop.txt", doc_text.encode("utf-8"), "text/plain")}
    r = await client_a.post("/api/documents/upload", files=files)
    doc_id = None
    if r.status_code == 201:
        doc_id = r.json().get("id")
    print(f"POST /api/documents/upload (Valid File): {r.status_code} -> Doc ID: {doc_id}")

    if doc_id:
        # Check processing status
        await asyncio.sleep(1)
        r = await client_a.get(f"/api/documents/{doc_id}/status")
        print(f"GET /api/documents/{{id}}/status: {r.status_code} -> {r.json().get('status')}")

        # User B accessing User A's document metadata
        r = await client_b.get(f"/api/documents/{doc_id}")
        print(f"GET /api/documents/{{id}} (Cross-User Isolation): {r.status_code} (Expected 404/403)")

        # Delete document
        r = await client_a.delete(f"/api/documents/{doc_id}")
        print(f"DELETE /api/documents/{{id}}: {r.status_code}")

    # 6. Preferences Endpoint Testing
    print("\n--- 6. User Preferences Endpoints ---")
    
    # Read preferences
    r = await client_a.get("/api/preferences")
    print(f"GET /api/preferences: {r.status_code} -> {r.json()}")

    # Write preferences
    r = await client_a.put("/api/preferences", json={"default_workspace": "general", "composer_behavior": "ctrl_enter"})
    print(f"PUT /api/preferences: {r.status_code}")

    # Write invalid preferences
    r = await client_a.put("/api/preferences", json={"default_workspace": "invalid_mode_name"})
    print(f"PUT /api/preferences (Invalid value): {r.status_code} (Expected 422/400)")

    # 7. Workspaces Selection
    print("\n--- 7. Workspaces Endpoints ---")
    r = await client_a.get("/api/workspaces")
    print(f"GET /api/workspaces: {r.status_code} -> Count: {len(r.json())}")

    # Cleanup
    await client_a.aclose()
    await client_b.aclose()
    print("==============================================")
    print("NOVA AI — Test Harness Run Completed")
    print("==============================================")

if __name__ == "__main__":
    asyncio.run(run_harness())
