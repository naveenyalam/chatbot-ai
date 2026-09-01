import asyncio
import httpx
import json
import uuid
import sys

async def run_e2e_test():
    base_url = "http://127.0.0.1:8000"
    client = httpx.AsyncClient(timeout=60.0)

    # 1. Register a new user
    email = f"alex.{uuid.uuid4().hex[:6]}@example.com"
    print(f"Registering user with email: {email}")
    reg_resp = await client.post(
        f"{base_url}/api/auth/register",
        json={"email": email, "password": "TestPassword123!", "name": "Alex"}
    )
    
    if reg_resp.status_code != 201:
        print(f"Registration failed: {reg_resp.status_code} - {reg_resp.text}")
        await client.aclose()
        sys.exit(1)
        
    print("Registration successful!")

    # Helper function to send chat message and accumulate response
    async def send_chat(messages, conversation_id=None):
        payload = {
            "messages": messages,
            "mode": "general",
            "workspace_mode": "general",
            "conversation_id": conversation_id,
            "model": "llama3.2:1b",
            "temperature": 0.3
        }
        
        headers = {"Content-Type": "application/json"}
        response_text = ""
        current_conv_id = conversation_id
        
        async with client.stream("POST", f"{base_url}/api/chat/stream", json=payload, headers=headers) as response:
            if response.status_code != 200:
                print(f"Request failed with status {response.status_code}")
                body = await response.aread()
                print(f"Error detail: {body.decode()}")
                return None, None
                
            async for line in response.aiter_lines():
                if not line:
                    continue
                print(f"[RAW LINE] {line}")
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        if event["type"] == "conversation_id":
                            current_conv_id = event["value"]
                        elif event["type"] == "text":
                            token = event["value"]
                            response_text += token
                        elif event["type"] == "error":
                            print(f"[ERROR EVENT] {event['value']}")
                    except Exception as e:
                        print(f"[PARSING ERROR] {e} on line {line}")
        return response_text, current_conv_id

    # Test prompts
    conversation_id = None
    prompts = [
        "hi",
        "What is Python?",
        "What is 25 * 48?",
        "What is the capital of India?",
        "Explain machine learning simply.",
        "Write a Python program to check whether a number is prime.",
        "Write a Java binary search program.",
        "My name is Alex.",
        "What is my name?"
    ]
    
    messages_history = []
    
    for idx, prompt in enumerate(prompts):
        if idx > 0:
            print("\nWaiting 2 seconds for Ollama to settle...")
            await asyncio.sleep(2.0)
            
        print(f"\n--- Prompt {idx+1}: {prompt} ---")
        messages_history.append({"role": "user", "content": prompt})
        
        response_text, new_conv_id = await send_chat(messages_history, conversation_id)
        if response_text is None:
            print("Failed to get response. Stopping E2E test.")
            break
            
        print(f"\nFinal Response: '{response_text}'")
        conversation_id = new_conv_id
        
        # If response was empty, default it to a placeholder so it doesn't fail Pydantic min_length=1
        if not response_text:
            response_text = "Empty response received."
            
        messages_history.append({"role": "assistant", "content": response_text})
        
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
