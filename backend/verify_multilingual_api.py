import httpx
import json
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    # 1. Initialize client with cookie support
    client = httpx.Client(timeout=300.0)
    
    # 2. Register a new user with a unique email to avoid duplicates
    email = f"qa_tester_{random.randint(1000, 9999)}@example.com"
    reg_payload = {
        "name": "QA Tester",
        "email": email,
        "password": "Password123!"
    }
    
    print("Registering test user...")
    res = client.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if res.status_code not in (200, 201):
        print(f"Failed to register: {res.status_code} - {res.text}")
        sys.exit(1)
        
    print(f"Successfully registered user: {email}")

    print("Logging in test user...")
    login_payload = {
        "email": email,
        "password": reg_payload["password"]
    }
    res = client.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"Failed to login: {res.status_code} - {res.text}")
        sys.exit(1)
    print("Successfully logged in.")
    
    # Helper to stream chat responses
    def stream_chat(messages, conversation_id=None, language="auto"):
        payload = {
            "messages": messages,
            "conversation_id": conversation_id,
            "language": language,
            "workspace_mode": "general",
            "temperature": 0.3
        }
        
        response_text = ""
        conv_id = conversation_id
        
        with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload) as r:
            if r.status_code != 200:
                print(f"Error status code: {r.status_code}")
                return "", None
            
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
                            val = event.get("value", "")
                            response_text += val
                            print(val, end="", flush=True)
                        elif event.get("type") == "error":
                            print(f"\n[SERVER ERROR] {event.get('value')}")
                    except Exception as e:
                        print(f"\n[JSON PARSE ERROR] {e} for line: {line}")
        print()
        return response_text, conv_id

    results = []

    # TEST 1: English
    print("\n--- TEST 1: English ---")
    print("Prompt: What is the capital of India?")
    ans_1, conv_1 = stream_chat([{"role": "user", "content": "What is the capital of India?"}])
    results.append(("TEST 1: English", ans_1))

    # TEST 2: Telugu
    print("\n--- TEST 2: Telugu ---")
    print("Prompt: భారతదేశ రాజధాని ఏది?")
    ans_2, conv_2 = stream_chat([{"role": "user", "content": "భారతదేశ రాజధాని ఏది?"}])
    results.append(("TEST 2: Telugu", ans_2))

    # TEST 3: Hindi
    print("\n--- TEST 3: Hindi ---")
    print("Prompt: भारत की राजधानी क्या है?")
    ans_3, conv_3 = stream_chat([{"role": "user", "content": "भारत की राजधानी क्या है?"}])
    results.append(("TEST 3: Hindi", ans_3))

    # TEST 4: Kannada
    print("\n--- TEST 4: Kannada ---")
    print("Prompt: ಭಾರತದ ರಾಜಧಾನಿ ಯಾವುದು?")
    ans_4, conv_4 = stream_chat([{"role": "user", "content": "ಭಾರತದ ರಾಜಧಾನಿ ಯಾವುದು?"}])
    results.append(("TEST 4: Kannada", ans_4))

    # TEST 5: Tamil
    print("\n--- TEST 5: Tamil ---")
    print("Prompt: இந்தியாவின் தலைநகரம் எது?")
    ans_5, conv_5 = stream_chat([{"role": "user", "content": "இந்தியாவின் தலைநகரம் எது?"}])
    results.append(("TEST 5: Tamil", ans_5))

    # TEST 6: Mixed English + Telugu
    print("\n--- TEST 6: Mixed English + Telugu ---")
    print("Prompt: India గురించి తెలుగులో చెప్పండి")
    ans_6, conv_6 = stream_chat([{"role": "user", "content": "India గురించి తెలుగులో చెప్పండి"}])
    results.append(("TEST 6: Mixed English + Telugu", ans_6))

    # TEST 7: Conversation switching
    print("\n--- TEST 7: Conversation switching (Turn 1) ---")
    print("Prompt: Tell me about India.")
    ans_7a, conv_7 = stream_chat([{"role": "user", "content": "Tell me about India."}])
    
    print("\n--- TEST 7: Conversation switching (Turn 2) ---")
    print("Prompt: ఇది తెలుగులో చెప్పండి.")
    # Include history and previous conversation_id
    messages_history = [
        {"role": "user", "content": "Tell me about India."},
        {"role": "assistant", "content": ans_7a},
        {"role": "user", "content": "ఇది తెలుగులో చెప్పండి."}
    ]
    ans_7b, _ = stream_chat(messages_history, conversation_id=conv_7)
    results.append(("TEST 7: Conv switching Turn 1 (English)", ans_7a))
    results.append(("TEST 7: Conv switching Turn 2 (Telugu)", ans_7b))

    # Save to file
    with open("verify_multilingual_results.txt", "w", encoding="utf-8") as f:
        for title, ans in results:
            f.write(f"\n=====================================\n{title}\n=====================================\n{ans}\n")
    print("\nAll end-to-end API tests complete. Results written to verify_multilingual_results.txt.")

if __name__ == "__main__":
    run_tests()
