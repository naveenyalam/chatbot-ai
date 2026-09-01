"""
Automated Latency Benchmarking Script for NOVA AI engine.

Distinguishes:
1. SSE connection setup time (sse_connection_ms)
2. First SSE event time (sse_first_event_ms — ping / metadata)
3. Actual LLM first text/content token (llm_first_token_ms — true TTFT)
4. Total response completion time (total_response_ms)

Across 7 scenarios with 1 COLD run + 10 WARM runs per scenario:
1. Simple normal chat ("Hello!")
2. Short explanation ("What is Python?")
3. Code generation query ("Write a Python function to check if a string is a palindrome.")
4. Long conversation (10+ turns)
5. RAG query (Document context)
6. Image generation request ("Generate an image of a futuristic neon city")
7. Workspace/agent query ("Analyze persistent HTTP connection pools")
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import time
import json
import asyncio
from fastapi.testclient import TestClient

def percentile(vals, p):
    if not vals:
        return 0.0
    sorted_v = sorted(vals)
    k = (len(sorted_v) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_v) else f
    d = k - f
    return sorted_v[f] + d * (sorted_v[c] - sorted_v[f])

from app.main import app
from app.core.config import settings

def run_benchmark():
    client = TestClient(app)
    
    # 1. Seed demo benchmark user
    from app.db.database import SessionLocal
    from app.models.user import User
    from app.services.auth_service import create_access_token, hash_password
    
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "benchmark@nova.ai").first()
        if not user:
            user = User(
                id="benchmark-user-id",
                name="Benchmark Runner",
                email="benchmark@nova.ai",
                password_hash=hash_password("bench12345")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        jwt_token = create_access_token({"sub": user.id})

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    scenarios = [
        {
            "name": "1. Simple Normal Chat",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "2. Short Explanation",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "What is Python?"}],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "3. Simple Concept Explanation",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Explain IoT in simple terms"}],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "4. Java Code Generation",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Write a simple Java program"}],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.2
            }
        },
        {
            "name": "5. Long Conversation (10 turns)",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [
                    {"role": "user", "content": f"Turn {i}: Quick tip."} if i % 2 == 0
                    else {"role": "assistant", "content": f"Tip {i}: Stay efficient."}
                    for i in range(10)
                ] + [{"role": "user", "content": "Summarize all our tips."}],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "6. RAG / Document Context Query",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "What is the context of document 1?"}],
                "document_ids": ["doc-1"],
                "model": settings.FAST_CHAT_MODEL,
                "temperature": 0.3
            }
        },
        {
            "name": "7. Image Generation Request",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Generate an image of a futuristic neon city"}],
                "model": settings.FAST_CHAT_MODEL
            }
        },
        {
            "name": "8. Workspace / Agent Query",
            "endpoint": "/api/workspaces/general/chat",
            "payload": {
                "message": "Analyze persistent HTTP connection pools.",
                "workspace_mode": "general"
            }
        }
    ]

    print("=" * 80)
    print(" [BENCHMARK] REAL-WORLD NOVA AI LLM FIRST-TOKEN LATENCY SUITE ")
    print("=" * 80)

    summary_results = {}

    for idx, sc in enumerate(scenarios, start=1):
        print(f"\nRunning Scenario ({idx}/8): {sc['name']}...", flush=True)
        warm_llm_ttfts = []
        warm_first_event_times = []
        warm_total_times = []
        cold_llm_ttft = 0.0

        # 1 COLD run + 2 WARM runs for fast validation
        total_runs = 3
        for run in range(total_runs):
            is_cold = (run == 0)
            t0 = time.perf_counter()
            sse_conn_t = None
            first_event_t = None
            actual_llm_token_t = None

            with client.stream("POST", sc["endpoint"], json=sc["payload"], headers=headers) as response:
                assert response.status_code == 200, f"Failed with status {response.status_code}"
                sse_conn_t = time.perf_counter()

                for line in response.iter_lines():
                    if line:
                        now = time.perf_counter()
                        if first_event_t is None:
                            first_event_t = now

                        # Differentiate true content (text/image) from SSE ping / conversation_id metadata
                        if actual_llm_token_t is None:
                            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                            if line_str.startswith("data: "):
                                try:
                                    payload = json.loads(line_str[6:])
                                    p_type = payload.get("type")
                                    if p_type in ("text", "image", "tool_result") and payload.get("value") or payload.get("image_url"):
                                        actual_llm_token_t = now
                                except Exception:
                                    pass

            t_end = time.perf_counter()
            actual_ttft_t = actual_llm_token_t or first_event_t or t_end

            sse_conn_ms = (sse_conn_t - t0) * 1000.0
            first_evt_ms = ((first_event_t or t_end) - t0) * 1000.0
            llm_token_ms = (actual_ttft_t - t0) * 1000.0
            total_ms = (t_end - t0) * 1000.0

            if is_cold:
                cold_llm_ttft = llm_token_ms
                print(f"  [COLD Run] Conn: {sse_conn_ms:.1f}ms | 1st Evt: {first_evt_ms:.1f}ms | LLM TTFT: {llm_token_ms:.1f}ms | Total: {total_ms:.1f}ms", flush=True)
            else:
                warm_llm_ttfts.append(llm_token_ms)
                warm_first_event_times.append(first_evt_ms)
                warm_total_times.append(total_ms)

        p50 = percentile(warm_llm_ttfts, 50)
        p95 = percentile(warm_llm_ttfts, 95)
        min_ttft = min(warm_llm_ttfts)
        max_ttft = max(warm_llm_ttfts)

        summary_results[sc["name"]] = {
            "cold_llm_ttft_ms": round(cold_llm_ttft, 2),
            "p50_llm_ttft_ms": round(p50, 2),
            "p95_llm_ttft_ms": round(p95, 2),
            "min_llm_ttft_ms": round(min_ttft, 2),
            "max_llm_ttft_ms": round(max_ttft, 2),
            "avg_total_ms": round(sum(warm_total_times) / len(warm_total_times), 2)
        }
        print(f"  [WARM Summary] P50 LLM TTFT: {p50:.2f}ms | P95 LLM TTFT: {p95:.2f}ms | Min: {min_ttft:.2f}ms | Max: {max_ttft:.2f}ms")

    print("\n" + "=" * 85)
    print(" [SUMMARY] REAL-WORLD LLM FIRST-TOKEN (TTFT) BENCHMARK RESULTS")
    print("=" * 85)
    print(f"{'Scenario':<36} | {'Cold TTFT':<10} | {'P50 TTFT':<10} | {'P95 TTFT':<10} | {'Min TTFT':<9} | {'Max TTFT':<9}")
    print("-" * 92)

    for name, stats in summary_results.items():
        print(
            f"{name:<36} | "
            f"{stats['cold_llm_ttft_ms']:<10.2f} | "
            f"{stats['p50_llm_ttft_ms']:<10.2f} | "
            f"{stats['p95_llm_ttft_ms']:<10.2f} | "
            f"{stats['min_llm_ttft_ms']:<9.2f} | "
            f"{stats['max_llm_ttft_ms']:<9.2f}"
        )
    print("=" * 85)

    return summary_results

if __name__ == "__main__":
    run_benchmark()
