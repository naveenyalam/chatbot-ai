import httpx
import json
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def debug_switching():
    client = httpx.Client(timeout=300.0)
    email = f"qa_debug_{random.randint(1000, 9999)}@example.com"
    reg = client.post(f"{BASE_URL}/api/auth/register", json={
        "name": "QA Debugger",
        "email": email,
        "password": "Password123!"
    })
    print(f"Register status: {reg.status_code}")
    
    # Turn 1
    payload1 = {
        "messages": [{"role": "user", "content": "Tell me about India."}],
        "language": "auto",
        "workspace_mode": "general",
        "temperature": 0.3
    }
    print("Sending Turn 1...")
    ans_7a = ""
    conv_id = None
    with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload1) as r:
        print(f"Turn 1 response code: {r.status_code}")
        for line in r.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    if event.get("type") == "conversation_id":
                        conv_id = event.get("value")
                    elif event.get("type") == "text":
                        ans_7a += event.get("value", "")
                except Exception as e:
                    print(f"Error parsing json in Turn 1: {e}")
                    
    print(f"Turn 1 complete. Conv ID: {conv_id}. Length of response: {len(ans_7a)}")
    
    # Turn 2
    messages_history = [
        {"role": "user", "content": "Tell me about India."},
        {"role": "assistant", "content": ans_7a},
        {"role": "user", "content": "ఇది తెలుగులో చెప్పండి."}
    ]
    payload2 = {
        "messages": messages_history,
        "conversation_id": conv_id,
        "language": "auto",
        "workspace_mode": "general",
        "temperature": 0.3
    }
    
    print("Sending Turn 2...")
    with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload2) as r:
        print(f"Turn 2 response code: {r.status_code}")
        print("Headers:")
        for k, v in r.headers.items():
            print(f"  {k}: {v}")
        print("Streaming lines:")
        for line in r.iter_lines():
            print(f"RAW LINE: {line}")

if __name__ == "__main__":
    debug_switching()
