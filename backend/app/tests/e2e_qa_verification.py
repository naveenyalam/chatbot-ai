import httpx
import json
import time
import uuid
import asyncio

BASE_URL = "http://localhost:8000"

def log_test(name, success, message=""):
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {name} - {message}")

async def run_e2e_tests():
    print("==============================================")
    print("NOVA AI — Phase 24 E2E QA Verification Suite")
    print("==============================================")

    # Setup httpx clients (which manage cookies/session context automatically)
    client_a = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
    client_b = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)

    test_id = str(uuid.uuid4())[:8]
    email_a = f"usera_{test_id}@nova.ai"
    email_b = f"userb_{test_id}@nova.ai"
    password = "SecurePassword123"

    # ==========================================
    # 1. AUTHENTICATION LIFECYCLE
    # ==========================================
    # Register User A
    reg_payload = {"email": email_a, "password": password, "name": "User A"}
    r = await client_a.post("/api/auth/register", json=reg_payload)
    log_test("Auth: Register User A", r.status_code == 201, f"Status: {r.status_code}")

    # Register User B
    reg_payload_b = {"email": email_b, "password": password, "name": "User B"}
    r = await client_b.post("/api/auth/register", json=reg_payload_b)
    log_test("Auth: Register User B", r.status_code == 201, f"Status: {r.status_code}")

    # Duplicate Registration check
    r = await client_a.post("/api/auth/register", json=reg_payload)
    log_test("Auth: Duplicate Email Blocked", r.status_code == 400, f"Status: {r.status_code}")

    # Login User A with invalid password
    r = await client_a.post("/api/auth/login", json={"email": email_a, "password": "WrongPassword"})
    log_test("Auth: Login Invalid Password Blocked", r.status_code == 401, f"Status: {r.status_code}")

    # Login User A successfully
    r = await client_a.post("/api/auth/login", json={"email": email_a, "password": password})
    log_test("Auth: Login User A Success", r.status_code == 200, f"Status: {r.status_code}")
    
    # Check current user /me
    r = await client_a.get("/api/auth/me")
    user_email = r.json().get("user", {}).get("email")
    log_test("Auth: Retrieve Profile (/me)", r.status_code == 200 and user_email == email_a, f"User: {user_email}")

    # Login User B successfully
    r = await client_b.post("/api/auth/login", json={"email": email_b, "password": password})
    log_test("Auth: Login User B Success", r.status_code == 200, f"Status: {r.status_code}")

    # Access without token
    anon_client = httpx.AsyncClient(base_url=BASE_URL)
    r = await anon_client.get("/api/conversations")
    log_test("Auth: Block Anonymous Access", r.status_code == 401, f"Status: {r.status_code}")
    await anon_client.aclose()

    # ==========================================
    # 2. CONVERSATION LIFECYCLE & ISOLATION
    # ==========================================
    # Create conversation as User A
    r = await client_a.post("/api/conversations", json={"title": f"User A Chat {test_id}"})
    assert r.status_code == 201, "Failed to create conversation for User A"
    conv_a = r.json()
    conv_a_id = conv_a.get("id")
    log_test("Conv: Create Conversation (User A)", conv_a_id is not None, f"ID: {conv_a_id}")

    # Create conversation as User B
    r = await client_b.post("/api/conversations", json={"title": f"User B Chat {test_id}"})
    assert r.status_code == 201
    conv_b_id = r.json().get("id")

    # List conversations for User A
    r = await client_a.get("/api/conversations")
    titles = [c.get("title") for c in r.json()]
    log_test("Conv: List Conversations", f"User A Chat {test_id}" in titles, f"Count: {len(titles)}")

    # Owner isolation: User B attempts to access User A's conversation
    r = await client_b.get(f"/api/conversations/{conv_a_id}")
    log_test("Conv: Ownership Isolation (User B reads User A's Chat)", r.status_code == 404 or r.status_code == 403, f"Status: {r.status_code}")

    # ==========================================
    # 3. REAL AI CHAT & STREAMING
    # ==========================================
    # We will test all 20 prompts (10 requested, 10 audit) and write to a JSON file to build the report.
    prompts = [
        # User 10 prompts
        "hi",
        "What is Python?",
        "What is 25 * 4?",
        "Write a Python function to calculate factorial.",
        "Explain REST API in simple terms.",
        "Give me 5 advantages of Redis.",
        "What is the capital of France?",
        "Summarize this text: \"Artificial intelligence allows computers to perform tasks that normally require human intelligence.\"",
        "Write a Java program to reverse a string.",
        "Explain recursion with an example.",
        # Audit 10 prompts
        "What framework does the backend use?",
        "What port does Redis use?",
        "Which frontend framework is used?",
        "What is the capital of Spain?",
        "Who wrote Romeo and Juliet?",
        "What is 10 + 15?",
        "Explain dark mode.",
        "Write a JavaScript arrow function.",
        "What is the speed of light?",
        "What is SQL?"
    ]

    quality_results = []
    
    print("\n--- Dispatching 20 AI Streaming Chat Requests ---")
    for idx, prompt in enumerate(prompts):
        start_time = time.time()
        
        # Dispatch stream request
        try:
            async with client_a.stream(
                "POST",
                "/api/chat/stream",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "conversation_id": conv_a_id,
                    "model": "nova-intelligence",
                    "temperature": 0.7
                }
            ) as r:
                full_response = ""
                events_received = []
                
                if r.status_code == 200:
                    async for line in r.aiter_lines():
                        if line:
                            events_received.append(line)
                            if line.startswith("data: "):
                                data_content = line[6:]
                                if data_content != "[DONE]":
                                    try:
                                        chunk = json.loads(data_content)
                                        # Handle chunk structure
                                        if chunk.get("type") == "text":
                                            full_response += chunk.get("value", "")
                                        elif chunk.get("type") == "conversation_id":
                                            pass
                                        else:
                                            # OpenAI shape fallback
                                            choices = chunk.get("choices", [])
                                            if choices:
                                                content = choices[0].get("delta", {}).get("content", "")
                                                full_response += content
                                    except Exception:
                                        pass
                                        
                    duration = time.time() - start_time
                    quality_results.append({
                        "prompt": prompt,
                        "actual_response": full_response.strip(),
                        "duration_seconds": round(duration, 3),
                        "events_count": len(events_received),
                        "status": "PASS"
                    })
                    log_test(f"AI Stream: Prompt #{idx+1} ({prompt[:25]}...)", True, f"Bytes: {len(full_response)} | time: {round(duration, 2)}s")
                else:
                    quality_results.append({
                        "prompt": prompt,
                        "actual_response": f"Error: Status {r.status_code}",
                        "duration_seconds": 0.0,
                        "events_count": 0,
                        "status": "FAIL"
                    })
                    log_test(f"AI Stream: Prompt #{idx+1} ({prompt[:25]}...)", False, f"Status: {r.status_code}")
        except Exception as exc:
            quality_results.append({
                "prompt": prompt,
                "actual_response": f"Exception: {exc}",
                "duration_seconds": 0.0,
                "events_count": 0,
                "status": "FAIL"
            })
            log_test(f"AI Stream: Prompt #{idx+1} ({prompt[:25]}...)", False, f"Exception: {exc}")

    # Save results to build the AI Quality Report
    with open("app/tests/ai_quality_results.json", "w") as f:
        json.dump(quality_results, f, indent=2)

    # ==========================================
    # 4. DOCUMENT RAG WORKFLOW & ISOLATION
    # ==========================================
    print("\n--- Testing Document RAG Pipeline ---")
    doc_content = (
        "Project NOVA was created in 2026.\n"
        "The project uses FastAPI.\n"
        "Redis runs on port 6379.\n"
        "The frontend uses Next.js.\n"
    )
    
    files = {"file": ("nova_info.txt", doc_content.encode("utf-8"), "text/plain")}
    # Upload document as User A
    r = await client_a.post("/api/documents/upload", files=files)
    doc_id = None
    if r.status_code == 201:
        doc_id = r.json().get("id")
    log_test("RAG: Upload Document (User A)", doc_id is not None, f"Doc ID: {doc_id}")

    if doc_id:
        # Wait for processing status to become completed
        status = "pending"
        for _ in range(10):
            r = await client_a.get(f"/api/documents/{doc_id}/status")
            status = r.json().get("status")
            if status == "indexed":
                break
            await asyncio.sleep(1)
        log_test("RAG: Document Processing Status", status == "indexed", f"Final Status: {status}")

        # Owner isolation: User B attempts to access User A's document
        r = await client_b.get(f"/api/documents/{doc_id}")
        log_test("RAG: Document Access Isolation", r.status_code == 404 or r.status_code == 403, f"Status: {r.status_code}")

        # Query Document via RAG /api/workspaces/documents/chat
        async with client_a.stream(
            "POST",
            "/api/workspaces/documents/chat",
            json={
                "messages": [{"role": "user", "content": "What framework does the backend use?"}],
                "conversation_id": conv_a_id,
                "model": "nova-intelligence",
                "temperature": 0.0
            }
        ) as r:
            rag_response = ""
            if r.status_code == 200:
                async for line in r.aiter_lines():
                    if line:
                        if line.startswith("data: "):
                            data_content = line[6:]
                            if data_content != "[DONE]":
                                try:
                                    chunk = json.loads(data_content)
                                    if chunk.get("type") == "text":
                                        rag_response += chunk.get("value", "")
                                    else:
                                        content = chunk.get("choices", [])[0].get("delta", {}).get("content", "")
                                        rag_response += content
                                except:
                                    pass
        log_test("RAG: Query 'What framework does the backend use?'", "FastAPI" in rag_response, f"Answer: {rag_response.strip()}")

        # Query 2
        async with client_a.stream(
            "POST",
            "/api/workspaces/documents/chat",
            json={
                "messages": [{"role": "user", "content": "What port does Redis use?"}],
                "conversation_id": conv_a_id,
                "model": "nova-intelligence",
                "temperature": 0.0
            }
        ) as r:
            rag_response2 = ""
            if r.status_code == 200:
                async for line in r.aiter_lines():
                    if line:
                        if line.startswith("data: "):
                            data_content = line[6:]
                            if data_content != "[DONE]":
                                try:
                                    chunk = json.loads(data_content)
                                    if chunk.get("type") == "text":
                                        rag_response2 += chunk.get("value", "")
                                    else:
                                        content = chunk.get("choices", [])[0].get("delta", {}).get("content", "")
                                        rag_response2 += content
                                except:
                                    pass
        log_test("RAG: Query 'What port does Redis use?'", "6379" in rag_response2, f"Answer: {rag_response2.strip()}")

        # Clean up document
        r = await client_a.delete(f"/api/documents/{doc_id}")
        log_test("RAG: Delete Document Metadata & Chunks", r.status_code == 200, f"Status: {r.status_code}")

    # ==========================================
    # 5. SETTINGS / PREFERENCES PERSISTENCE
    # ==========================================
    print("\n--- Testing Settings & Preferences ---")
    r = await client_a.put("/api/preferences", json={
        "default_workspace": "general",
        "composer_behavior": "ctrl_enter"
    })
    log_test("Settings: Save Preferences", r.status_code == 200, f"Status: {r.status_code}")

    # Retrieve settings
    r = await client_a.get("/api/preferences")
    pref = r.json()
    log_test("Settings: Verify Persistence", pref.get("default_workspace") == "general" and pref.get("composer_behavior") == "ctrl_enter", f"Saved: {pref}")

    # ==========================================
    # 6. LOGOUT CLEANUP
    # ==========================================
    r = await client_a.post("/api/auth/logout")
    log_test("Auth: Logout User A", r.status_code == 200, f"Status: {r.status_code}")
    
    r = await client_a.get("/api/conversations")
    log_test("Auth: Session Cleared Post-Logout", r.status_code == 401, f"Status: {r.status_code}")

    await client_a.aclose()
    await client_b.aclose()
    print("==============================================")
    print("NOVA AI — E2E QA Verification Complete")
    print("==============================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
