import os
import sys
import time
import json
import statistics
import httpx
import pytest

PROD_BACKEND_URL = os.getenv("PROD_BACKEND_URL", "https://nova-ai-backend.onrender.com")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL", "https://nova-ai-chat-pi.vercel.app")

TEST_PROMPTS = [
    "Hello",
    "Explain Python in simple words.",
    "What is an API?",
    "Write a small Java program.",
    "Explain what AI is.",
    "Hello again!",
    "How does web streaming work?",
    "Explain cloud computing.",
    "Write a hello world in C++.",
    "What is database index?"
]

MAX_FIRST_TOKEN_LATENCY_SECONDS = 10.0

def run_single_chat_latency_test(backend_url: str, prompt: str) -> dict:
    """
    Executes a single SSE chat streaming request and records precise lifecycle timestamps:
    T0 = Request start
    T1 = Response headers received (connection established)
    T2 = First SSE event received (ping/metadata)
    T3 = FIRST REAL NON-EMPTY ASSISTANT CONTENT TOKEN (Real TTFT)
    T4 = Stream completion
    """
    endpoint = f"{backend_url.rstrip('/')}/api/workspaces/general/chat"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Origin": PROD_FRONTEND_URL,
        "User-Agent": "NOVA-AI-RealLatencyTest/1.0"
    }
    payload = {
        "message": prompt,
        "history": [],
        "workspace_mode": "general",
        "model": "nova-fast"
    }

    t0 = time.perf_counter()
    t1_headers = None
    t2_first_sse = None
    t3_first_content_token = None
    t4_done = None
    first_token_text = ""
    received_tokens_count = 0
    non_content_events_count = 0

    try:
        if backend_url.startswith("http"):
            with httpx.Client(timeout=35.0) as client:
                with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    t1_headers = time.perf_counter()
                    if response.status_code != 200:
                        return {"prompt": prompt, "status_code": response.status_code, "success": False, "error": f"HTTP {response.status_code}"}

                    for line in response.iter_lines():
                        now = time.perf_counter()
                        if not line:
                            continue
                        if not t2_first_sse:
                            t2_first_sse = now

                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                event_data = json.loads(data_str)
                            except Exception:
                                continue

                            event_type = event_data.get("type")
                            if event_type in ("ping", "heartbeat", "metadata", "latency_breakdown", "conversation_id", "status", "message_start"):
                                non_content_events_count += 1
                                continue

                            content = event_data.get("value") or event_data.get("content") or event_data.get("text") or ""
                            if content and event_type == "text":
                                if t3_first_content_token is None:
                                    t3_first_content_token = now
                                    first_token_text = content
                                received_tokens_count += 1

                    t4_done = time.perf_counter()
        else:
            from fastapi.testclient import TestClient
            from app.main import app
            client = TestClient(app)
            with client.stream("POST", "/api/workspaces/general/chat", headers=headers, json=payload) as response:
                t1_headers = time.perf_counter()
                if response.status_code != 200:
                    return {"prompt": prompt, "status_code": response.status_code, "success": False, "error": f"HTTP {response.status_code}"}

                for line in response.iter_lines():
                    now = time.perf_counter()
                    if not line:
                        continue
                    if not t2_first_sse:
                        t2_first_sse = now

                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            event_data = json.loads(data_str)
                        except Exception:
                            continue

                        event_type = event_data.get("type")
                        if event_type in ("ping", "heartbeat", "metadata", "latency_breakdown", "conversation_id", "status", "message_start"):
                            non_content_events_count += 1
                            continue

                        content = event_data.get("value") or event_data.get("content") or event_data.get("text") or ""
                        if content and event_type == "text":
                            if t3_first_content_token is None:
                                t3_first_content_token = now
                                first_token_text = content
                            received_tokens_count += 1

                t4_done = time.perf_counter()

        # Latency calculations in milliseconds
        conn_ms = (t1_headers - t0) * 1000 if t1_headers else 0.0
        first_sse_ms = (t2_first_sse - t0) * 1000 if t2_first_sse else 0.0
        
        # REAL TTFT: measured at t3_first_content_token
        real_ttft_sec = (t3_first_content_token - t0) if t3_first_content_token else (t4_done - t0)
        real_ttft_ms = real_ttft_sec * 1000
        total_duration_ms = (t4_done - t0) * 1000

        is_success = bool(t3_first_content_token and real_ttft_sec <= MAX_FIRST_TOKEN_LATENCY_SECONDS)

        return {
            "prompt": prompt,
            "status_code": 200,
            "success": is_success,
            "sse_connection_ms": round(conn_ms, 2),
            "sse_first_event_ms": round(first_sse_ms, 2),
            "real_llm_first_token_ms": round(real_ttft_ms, 2),
            "real_llm_first_token_sec": round(real_ttft_sec, 3),
            "first_content_preview": repr(first_token_text[:20]),
            "non_content_events": non_content_events_count,
            "tokens_received": received_tokens_count,
            "total_response_ms": round(total_duration_ms, 2)
        }

    except Exception as exc:
        return {
            "prompt": prompt,
            "status_code": 0,
            "success": False,
            "error": str(exc)
        }

def compute_percentiles(values: list) -> dict:
    if not values:
        return {"min": 0, "avg": 0, "p50": 0, "p95": 0, "max": 0}
    s = sorted(values)
    n = len(s)
    def p(pct):
        k = (n - 1) * (pct / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        return s[f] + (k - f) * (s[c] - s[f])
    return {
        "min": round(min(s), 2),
        "avg": round(statistics.mean(s), 2),
        "p50": round(p(50), 2),
        "p95": round(p(95), 2),
        "max": round(max(s), 2)
    }

def print_benchmark_report(title: str, results: list):
    print(f"\n==================================================")
    print(f"  {title}")
    print(f"==================================================")
    
    ttfts = [r["real_llm_first_token_ms"] for r in results if r.get("success")]

    for i, r in enumerate(results, 1):
        if r.get("success"):
            print(f"[{i:02d}] Prompt: '{r['prompt'][:30]:<30}' | Conn: {r['sse_connection_ms']:>6.1f}ms | First Event: {r['sse_first_event_ms']:>6.1f}ms | REAL TTFT: {r['real_llm_first_token_ms']:>7.1f}ms | Total: {r['total_response_ms']:>7.1f}ms | Token: {r['first_content_preview']}")
        else:
            print(f"[{i:02d}] Prompt: '{r['prompt'][:30]:<30}' | FAILED: {r.get('error') or r.get('status_code')}")

    print("\n--- LATENCY SUMMARY (REAL FIRST ASSISTANT CONTENT TOKEN) ---")
    stats = compute_percentiles(ttfts)
    print(f"  Min TTFT:      {stats['min']:>8.2f} ms")
    print(f"  Avg TTFT:      {stats['avg']:>8.2f} ms")
    print(f"  P50 TTFT:      {stats['p50']:>8.2f} ms")
    print(f"  P95 TTFT:      {stats['p95']:>8.2f} ms")
    print(f"  Max TTFT:      {stats['max']:>8.2f} ms")
    print(f"  Pass Rate:     {len(ttfts)}/{len(results)} ({len(ttfts)/len(results)*100:.1f}%)")

@pytest.mark.parametrize("prompt", TEST_PROMPTS[:3])
def test_real_chat_latency_threshold(prompt, monkeypatch):
    from app.core.config import settings
    from app.api.routes.auth import get_current_user
    from app.models.user import User
    from app.main import app
    from app.services.model_router import model_router
    from app.services.llm_provider import MockLLMProvider

    mock_user = User(id="test-user-id", email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    monkeypatch.setattr(settings, "AI_USE_MOCK", True)
    monkeypatch.setattr(model_router, "_provider", MockLLMProvider())

    try:
        # Pre-warm app state for test execution
        run_single_chat_latency_test("testclient", "warmup")
        res = run_single_chat_latency_test("testclient", prompt)
        assert res.get("success") is True, f"Chat latency test failed for '{prompt}': {res}"
        assert res["real_llm_first_token_sec"] < MAX_FIRST_TOKEN_LATENCY_SECONDS
    finally:
        app.dependency_overrides.pop(get_current_user, None)

if __name__ == "__main__":
    target_backend = sys.argv[1] if len(sys.argv) > 1 else PROD_BACKEND_URL
    print(f"Starting Real Chat Latency Benchmark against: {target_backend}")
    results = []
    for prompt in TEST_PROMPTS:
        res = run_single_chat_latency_test(target_backend, prompt)
        results.append(res)
        time.sleep(0.5)

    print_benchmark_report(f"BENCHMARK RESULTS ({target_backend})", results)
