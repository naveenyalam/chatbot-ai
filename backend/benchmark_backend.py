import httpx
import json
import time
import sys
import random
import asyncio

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b"

def unload_model():
    print(f"Unloading model {MODEL}...")
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": MODEL, "keep_alive": 0}, timeout=10.0)
        if r.status_code == 200:
            print("Unload command sent successfully.")
        else:
            print(f"Unload command failed: {r.status_code}")
    except Exception as e:
        print(f"Error unloading model: {e}")
    time.sleep(2)

async def run_backend_benchmark():
    # Create client
    client = httpx.AsyncClient(timeout=300.0)
    
    # Register user
    email = f"benchmark_tester_{random.randint(10000, 99999)}@example.com"
    reg_payload = {
        "name": "Benchmark Tester",
        "email": email,
        "password": "Password123!"
    }
    
    print(f"Registering tester {email}...")
    res = await client.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if res.status_code not in (200, 201):
        print(f"Registration failed: {res.status_code} - {res.text}")
        await client.aclose()
        return
        
    # Login
    login_payload = {
        "email": email,
        "password": "Password123!"
    }
    res = await client.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"Login failed: {res.status_code} - {res.text}")
        await client.aclose()
        return
        
    print("Successfully authenticated. Starting backend prompts...")
    
    prompts = [
        "Hi",
        "What is the capital of India?",
        "Explain Python in 5 points.",
        "తెలుగులో Python గురించి 5 పాయింట్లు చెప్పండి."
    ]
    
    results = []
    
    # We unload the model before the first prompt to get a cold start measurement
    unload_model()
    
    for idx, prompt in enumerate(prompts):
        print(f"\nRunning backend benchmark for prompt: '{prompt}'")
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "conversation_id": None,
            "language": "auto",
            "workspace_mode": "general",
            "temperature": 0.3
        }
        
        start_time = time.time()
        ttft = None
        response_text = ""
        chunks_count = 0
        
        try:
            async with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload) as r:
                if r.status_code != 200:
                    print(f"Failed to connect to stream: {r.status_code}")
                    continue
                    
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            if event.get("type") == "text":
                                chunk_time = time.time()
                                val = event.get("value", "")
                                if ttft is None and val:
                                    ttft = chunk_time - start_time
                                response_text += val
                                chunks_count += 1
                        except Exception as e:
                            pass
        except Exception as e:
            print(f"Streaming request failed: {e}")
            continue
            
        total_time = time.time() - start_time
        
        # Estimate tokens as char_len / 4
        est_tokens = len(response_text) / 4
        tokens_per_sec = est_tokens / total_time if total_time > 0 else 0
        
        res_data = {
            "prompt": prompt,
            "ttft_sec": ttft if ttft is not None else 0,
            "total_time_sec": total_time,
            "char_len": len(response_text),
            "est_tokens": est_tokens,
            "tokens_per_sec": tokens_per_sec,
            "response_preview": response_text[:100] + "..."
        }
        results.append(res_data)
        
        print(f"  TTFT: {res_data['ttft_sec']:.4f}s")
        print(f"  Total Time: {res_data['total_time_sec']:.4f}s")
        print(f"  Chars Generated: {res_data['char_len']} (~{res_data['est_tokens']:.1f} tokens)")
        print(f"  Est. Tokens/sec: {res_data['tokens_per_sec']:.2f}")
        
    await client.aclose()
    
    with open("backend_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nBackend benchmark complete. Results saved to backend_benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(run_backend_benchmark())
