import os
import sys
import time
import json
import httpx
import pytest

# Target live production URLs or local fallback
PROD_BACKEND_URL = os.getenv("PROD_BACKEND_URL", "https://nova-ai-backend.onrender.com")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL", "https://nova-ai-chat-pi.vercel.app")

TEST_PROMPTS = [
    "Hello",
    "What is Python?",
    "Explain IoT",
    "Write a simple Java program",
    "Summarize quantum computing"
]

MAX_ALLOWED_TTFT_SECONDS = 10.0

def measure_chat_ttft(prompt: str) -> dict:
    """
    Sends a real SSE streaming chat request to the target backend and measures:
    1. SSE Connection establish latency (connection_ms)
    2. Time to First Real LLM Content Token (ttft_seconds)
    3. Total stream duration (total_seconds)
    """
    endpoint = f"{PROD_BACKEND_URL}/api/workspaces/general/chat"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Origin": PROD_FRONTEND_URL,
        "User-Agent": "NOVA-AI-Production-Verification/1.0"
    }
    payload = {
        "message": prompt,
        "history": [],
        "workspace_mode": "general"
    }

    start_time = time.time()
    first_token_time = None
    first_token_text = ""
    received_tokens = 0
    connect_time = None

    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                connect_time = time.time() - start_time
                if response.status_code != 200:
                    return {
                        "prompt": prompt,
                        "status_code": response.status_code,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }

                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                    except Exception:
                        continue

                    # Ignore ping/heartbeat, metadata, and empty content
                    if data.get("type") in ("ping", "heartbeat", "metadata", "latency_breakdown"):
                        continue

                    content = data.get("content") or data.get("delta") or data.get("text") or ""
                    if content and not first_token_time:
                        first_token_time = time.time()
                        first_token_text = content
                    
                    if content:
                        received_tokens += 1

        total_duration = time.time() - start_time
        ttft = (first_token_time - start_time) if first_token_time else total_duration

        return {
            "prompt": prompt,
            "status_code": 200,
            "success": bool(first_token_time and ttft <= MAX_ALLOWED_TTFT_SECONDS),
            "connect_ms": round((connect_time or 0) * 1000, 2),
            "ttft_seconds": round(ttft, 3),
            "ttft_ms": round(ttft * 1000, 2),
            "first_token": first_token_text[:20],
            "tokens_received": received_tokens,
            "total_seconds": round(total_duration, 3)
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

@pytest.mark.parametrize("prompt", TEST_PROMPTS)
def test_production_ttft_under_10s(prompt):
    """Asserts that real production chat TTFT is strictly less than 10 seconds."""
    result = measure_chat_ttft(prompt)
    print(f"\n[PROMPT: '{prompt}'] -> TTFT: {result.get('ttft_seconds')}s (Success: {result.get('success')})")
    if not result.get("success"):
        pytest.fail(f"TTFT verification failed for prompt '{prompt}': {result}")
    assert result["ttft_seconds"] < MAX_ALLOWED_TTFT_SECONDS

if __name__ == "__main__":
    print(f"=== NOVA AI PRODUCTION TTFT BENCHMARK ===")
    print(f"Backend URL: {PROD_BACKEND_URL}")
    print(f"Frontend URL: {PROD_FRONTEND_URL}")
    print(f"Max Allowed TTFT: {MAX_ALLOWED_TTFT_SECONDS}s\n")
    
    results = []
    for prompt in TEST_PROMPTS:
        res = measure_chat_ttft(prompt)
        results.append(res)
        status = "PASSED" if res.get("success") else "FAILED"
        print(f"Prompt: '{prompt}' | Status: {status} | TTFT: {res.get('ttft_seconds')}s ({res.get('ttft_ms')}ms) | Connect: {res.get('connect_ms')}ms | First token: {repr(res.get('first_token'))}")
        time.sleep(1)

    print("\n=== SUMMARY ===")
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    print(f"Passed: {passed}/{total}")
    if passed < total:
        print("WARNING: Some benchmarks did not meet the target.")
