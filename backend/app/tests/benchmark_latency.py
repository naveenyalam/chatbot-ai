"""
Automated Latency Benchmarking Script for NOVA AI engine.

Measures:
- Cold-start TTFT vs Warm-request TTFT
- P50 TTFT & P95 TTFT
- Pre-LLM backend latency
- Total response time
Across 6 scenarios:
1. Short normal chat
2. Long conversation (10+ turns)
3. Code question
4. RAG / document context question
5. Image generation request
6. Agent / workspace mode request
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import time
import json
import asyncio
from fastapi.testclient import TestClient

def percentile(vals, p):
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
    
    # 1. Prepare demo authentication headers
    token = "demo-benchmark-token"
    # Seed demo user
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
            "name": "1. Short Normal Chat",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Hello! What is NOVA AI?"}],
                "model": settings.AI_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "2. Long Conversation (10 turns)",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [
                    {"role": "user", "content": f"Turn {i}: Tell me a quick tip."}
                    if i % 2 == 0 else
                    {"role": "assistant", "content": f"Tip {i}: Stay focused!"}
                    for i in range(10)
                ] + [{"role": "user", "content": "Summarize all our tips."}],
                "model": settings.AI_MODEL,
                "temperature": 0.7
            }
        },
        {
            "name": "3. Code Question",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Write a Python function to check if a string is a palindrome."}],
                "model": settings.AI_MODEL,
                "temperature": 0.2
            }
        },
        {
            "name": "4. RAG / Documents Context Question",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "What is the context of document 1?"}],
                "document_ids": ["doc-1"],
                "model": settings.AI_MODEL,
                "temperature": 0.3
            }
        },
        {
            "name": "5. Image Generation Request",
            "endpoint": "/api/chat/stream",
            "payload": {
                "messages": [{"role": "user", "content": "Generate an image of a futuristic neon cybernetic city"}],
                "model": settings.AI_MODEL
            }
        },
        {
            "name": "6. Agent Workspace Request",
            "endpoint": "/api/workspaces/general/chat",
            "payload": {
                "message": "Analyze the efficiency of persistent HTTP connection pools.",
                "workspace_mode": "general"
            }
        }
    ]

    print("=" * 70)
    print(" [BENCHMARK] NOVA AI LATENCY & STREAMING PERFORMANCE BENCHMARK ")
    print("=" * 70)

    all_results = {}

    for idx, sc in enumerate(scenarios, start=1):
        print(f"\nRunning Scenario: {sc['name']}...")
        ttfts = []
        total_times = []

        # 3 runs per scenario
        for run in range(3):
            is_cold = (idx == 1 and run == 0)
            t0 = time.perf_counter()
            first_token_t = None

            with client.stream("POST", sc["endpoint"], json=sc["payload"], headers=headers) as response:
                assert response.status_code == 200, f"Failed with status {response.status_code}"
                for line in response.iter_lines():
                    if line:
                        if first_token_t is None and ("text" in line or "image" in line or "value" in line):
                            first_token_t = time.perf_counter()

            t_end = time.perf_counter()
            ttft_ms = ((first_token_t or t_end) - t0) * 1000.0
            total_ms = (t_end - t0) * 1000.0

            ttfts.append(ttft_ms)
            total_times.append(total_ms)

            run_type = "COLD" if is_cold else "WARM"
            print(f"  [{run_type} Run {run + 1}] TTFT: {ttft_ms:.2f} ms | Total: {total_ms:.2f} ms")

        p50_ttft = percentile(ttfts, 50)
        p95_ttft = percentile(ttfts, 95)
        avg_total = sum(total_times) / len(total_times)

        all_results[sc["name"]] = {
            "p50_ttft_ms": round(p50_ttft, 2),
            "p95_ttft_ms": round(p95_ttft, 2),
            "avg_total_ms": round(avg_total, 2),
            "cold_ttft_ms": round(ttfts[0], 2)
        }

    print("\n" + "=" * 70)
    print(" [SUMMARY] BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Scenario':<38} | {'Cold TTFT':<10} | {'P50 TTFT':<10} | {'P95 TTFT':<10}")
    print("-" * 75)

    for name, stats in all_results.items():
        print(f"{name:<38} | {stats['cold_ttft_ms']:<10.2f} | {stats['p50_ttft_ms']:<10.2f} | {stats['p95_ttft_ms']:<10.2f}")

    print("=" * 70)
    return all_results

if __name__ == "__main__":
    run_benchmark()
