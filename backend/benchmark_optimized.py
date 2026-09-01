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

async def send_chat_stream(client, prompt, conversation_id=None, language="auto", messages_history=None):
    if messages_history is None:
        messages_history = []
        
    payload_messages = messages_history + [{"role": "user", "content": prompt}]
    
    payload = {
        "messages": payload_messages,
        "conversation_id": conversation_id,
        "language": language,
        "workspace_mode": "general",
        "temperature": 0.3,
        "model": "qwen2.5:3b"
    }
    
    start_time = time.time()
    ttft = None
    response_text = ""
    resolved_conv_id = conversation_id
    
    try:
        async with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload) as r:
            if r.status_code != 200:
                print(f"Failed to connect: {r.status_code}")
                return None
                
            async for line in r.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        if event.get("type") == "conversation_id":
                            resolved_conv_id = event.get("value")
                        elif event.get("type") == "text":
                            chunk_time = time.time()
                            val = event.get("value", "")
                            if ttft is None and val:
                                ttft = chunk_time - start_time
                            response_text += val
                    except Exception as e:
                        pass
    except Exception as e:
        print(f"Streaming request failed: {e}")
        return None
        
    total_time = time.time() - start_time
    est_tokens = len(response_text) / 4
    tps = est_tokens / total_time if total_time > 0 else 0
    
    # Update messages history in-place with user and assistant turns
    messages_history.append({"role": "user", "content": prompt})
    messages_history.append({"role": "assistant", "content": response_text})
    
    return {
        "prompt": prompt,
        "conversation_id": resolved_conv_id,
        "ttft_sec": ttft if ttft is not None else 0,
        "total_time_sec": total_time,
        "char_len": len(response_text),
        "est_tokens": est_tokens,
        "tokens_per_second": tps,
        "response": response_text
    }

async def run_benchmark():
    client = httpx.AsyncClient(timeout=300.0)
    
    # Register user
    email = f"opt_tester_{random.randint(10000, 99999)}@example.com"
    reg_payload = {
        "name": "Optimization Tester",
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
        
    print("Successfully authenticated. Starting optimized qwen2.5:3b benchmark...")
    
    prompts = [
        ("Hi", "auto"),
        ("What is the capital of India?", "auto"),
        ("Explain Python in 5 points.", "auto"),
        ("Explain IoT in simple terms.", "auto"),
        ("తెలుగులో Python గురించి 5 పాయిंట్లు చెప్పండి.", "auto"),
        ("हिंदी में Python समझाइए।", "auto"),
        ("ಕನ್ನಡದಲ್ಲಿ IoT ಬಗ್ಗೆ ವಿವರಿಸಿ.", "auto"),
        ("தமிழில் AI பற்றி விளக்குங்கள்.", "auto")
    ]
    
    results = []
    
    # 1. Unload model to get true Cold Start on first prompt
    unload_model("qwen2.5:3b")
    
    # 2. Run standard prompts (single-turn conversations)
    for idx, (prompt, lang) in enumerate(prompts):
        is_cold = (idx == 0)
        print(f"\nRunning Prompt {idx+1}/{len(prompts)}: '{prompt}' ({'COLD START' if is_cold else 'WARM START'})")
        res_data = await send_chat_stream(client, prompt, language=lang)
        if res_data:
            res_data["is_cold_start"] = is_cold
            results.append(res_data)
            print(f"  TTFT: {res_data['ttft_sec']:.4f}s")
            print(f"  Total Time: {res_data['total_time_sec']:.4f}s")
            print(f"  Length: {res_data['char_len']} chars (~{res_data['est_tokens']:.1f} tokens)")
            print(f"  Est. Tokens/sec: {res_data['tokens_per_second']:.2f}")
            print(f"  Preview: {res_data['response'][:100]}...")
            
    # 3. Run multi-turn conversation memory check
    print("\nStarting Multi-turn memory verification...")
    messages_history = []
    # Turn 1
    turn1_res = await send_chat_stream(client, "My name is John. Remember my name.", messages_history=messages_history)
    if turn1_res:
        conv_id = turn1_res["conversation_id"]
        print(f"  Turn 1 Complete. Conversation ID: {conv_id}")
        print(f"  Response: {turn1_res['response']}")
        
        # Turn 2
        turn2_res = await send_chat_stream(client, "What is my name?", conversation_id=conv_id, messages_history=messages_history)
        if turn2_res:
            print(f"  Turn 2 Complete.")
            print(f"  Response: {turn2_res['response']}")
            results.append({
                "prompt": "What is my name? (Multi-turn)",
                "conversation_id": conv_id,
                "ttft_sec": turn2_res["ttft_sec"],
                "total_time_sec": turn2_res["total_time_sec"],
                "char_len": turn2_res["char_len"],
                "est_tokens": turn2_res["est_tokens"],
                "tokens_per_second": turn2_res["tokens_per_second"],
                "response": turn2_res["response"],
                "is_multi_turn": True
            })
            
    await client.aclose()
    
    with open("benchmark_optimized_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nOptimized benchmark complete. Results saved to benchmark_optimized_results.json")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
