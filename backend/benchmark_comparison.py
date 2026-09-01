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

import os

def unload_model(model):
    print(f"Unloading model {model}...")
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": model, "keep_alive": 0}, timeout=10.0)
        if r.status_code == 200:
            print(f"Unload command for {model} sent successfully.")
        else:
            print(f"Unload command for {model} failed: {r.status_code}")
    except Exception as e:
        print(f"Error unloading model {model}: {e}")
    time.sleep(2)

async def run_benchmark():
    os.environ["MAX_GENERATION_TOKENS"] = "100"
    client = httpx.AsyncClient(timeout=300.0)
    
    # Register user
    email = f"comparison_tester_{random.randint(10000, 99999)}@example.com"
    reg_payload = {
        "name": "Comparison Tester",
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
        
    print("Successfully authenticated. Starting model comparison...")
    
    prompts = [
        "Hi",
        "What is the capital of India?",
        "Explain Python in 5 points.",
        "Explain IoT in simple terms.",
        "తెలుగులో Python గురించి 5 పాయింట్లు చెప్పండి.",
        "हिंदी में Python समझाइए।",
        "ಕನ್ನಡದಲ್ಲಿ IoT ಬಗ್ಗೆ ವಿವರಿಸಿ.",
        "தமிழில் AI பற்றி விளக்குங்கள்."
    ]
    
    models = ["qwen2.5:3b", "qwen2.5:1.5b"]
    all_results = {}
    
    for model in models:
        print(f"\n==================================================")
        print(f" BENCHMARKING MODEL: {model}")
        print(f"==================================================")
        
        # Unload model first to get cold-start for prompt 1
        unload_model(model)
        
        model_results = []
        
        for idx, prompt in enumerate(prompts):
            print(f"\nRunning {model} for prompt: '{prompt}'")
            
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "conversation_id": None,
                "language": "auto",
                "workspace_mode": "general",
                "temperature": 0.3,
                "model": model
            }
            
            start_time = time.time()
            ttft = None
            response_text = ""
            chunks_count = 0
            
            try:
                async with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload) as r:
                    if r.status_code != 200:
                        print(f"Failed to connect: {r.status_code}")
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
            
            # Count words and estimate tokens (char_len / 4)
            est_tokens = len(response_text) / 4
            tps = est_tokens / total_time if total_time > 0 else 0
            
            res_data = {
                "prompt": prompt,
                "ttft_sec": ttft if ttft is not None else 0,
                "total_time_sec": total_time,
                "char_len": len(response_text),
                "est_tokens": est_tokens,
                "tokens_per_second": tps,
                "response": response_text
            }
            model_results.append(res_data)
            
            print(f"  TTFT: {res_data['ttft_sec']:.4f}s")
            print(f"  Total Time: {res_data['total_time_sec']:.4f}s")
            print(f"  Length: {res_data['char_len']} chars (~{res_data['est_tokens']:.1f} tokens)")
            print(f"  Est. Tokens/sec: {res_data['tokens_per_second']:.2f}")
            print(f"  Preview: {response_text[:80]}...")
            
        all_results[model] = model_results
        
    await client.aclose()
    
    with open("model_comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print("\nModel comparison benchmark complete. Results saved to model_comparison_results.json")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
