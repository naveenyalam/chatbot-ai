import httpx
import json
import random
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://127.0.0.1:11434"
BACKEND_URL = "http://127.0.0.1:8000"
TARGET_MODEL = "qwen2.5:3b"

def detect_script(text: str) -> str:
    counts = {
        "Telugu": 0,
        "Hindi": 0,
        "Kannada": 0,
        "Tamil": 0
    }
    for char in text:
        cp = ord(char)
        if 0x0c00 <= cp <= 0x0c7f:
            counts["Telugu"] += 1
        elif 0x0900 <= cp <= 0x097f:
            counts["Hindi"] += 1
        elif 0x0c80 <= cp <= 0x0cff:
            counts["Kannada"] += 1
        elif 0x0b80 <= cp <= 0x0bff:
            counts["Tamil"] += 1
            
    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    return "English/Latin"

def test_ollama_status():
    print("[1/4] Checking Ollama Status & Model...")
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags")
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text}"
        models = [m["name"] for m in r.json().get("models", [])]
        if TARGET_MODEL in models:
            return True, f"Found model: {TARGET_MODEL}"
        # Fallback check for tag-less match
        for m in models:
            if m.startswith(TARGET_MODEL):
                return True, f"Found model: {m}"
        return False, f"Model '{TARGET_MODEL}' not found. Available: {models}"
    except Exception as e:
        return False, f"Could not connect to Ollama: {str(e)}"

def test_ollama_direct():
    print("[2/4] Verifying Direct Ollama Multilingual Capabilities...")
    prompts = {
        "Telugu": "భారతదేశ రాజధాని ఏది? ఒక్క ముక్కలో సమాధానం చెప్పండి.",
        "Hindi": "भारत की राजधानी क्या है? एक शब्द में उत्तर दें।",
        "Kannada": "ಭಾರತದ ರಾಜಧಾನಿ ಯಾವುದು? ಒಂದು ಪದದಲ್ಲಿ ಉತ್ತರಿಸಿ.",
        "Tamil": "இந்தியாவின் தலைநகரம் எது? ஒரு வார்த்தையில் பதிலளிக்கவும்."
    }
    results = {}
    for lang, prompt in prompts.items():
        try:
            payload = {
                "model": TARGET_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
            r = httpx.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60.0)
            if r.status_code == 200:
                resp_text = r.json().get("response", "").strip()
                detected = detect_script(resp_text)
                success = (detected == lang)
                results[lang] = {
                    "success": success,
                    "response": resp_text,
                    "detected_script": detected
                }
            else:
                results[lang] = {"success": False, "response": f"HTTP {r.status_code}", "detected_script": "N/A"}
        except Exception as e:
            results[lang] = {"success": False, "response": str(e), "detected_script": "N/A"}
    return results

def test_backend_status():
    print("[3/4] Verifying FastAPI health and readiness...")
    health_ok = False
    ready_ok = False
    
    try:
        r = httpx.get(f"{BACKEND_URL}/health")
        health_ok = (r.status_code == 200 and r.json().get("status") == "ok")
    except Exception as e:
        print(f"Health check failed: {e}")
        
    try:
        r = httpx.get(f"{BACKEND_URL}/ready")
        ready_ok = (r.status_code == 200 and r.json().get("status") == "healthy")
    except Exception as e:
        print(f"Ready check failed: {e}")
        
    return health_ok, ready_ok

def test_backend_chat():
    print("[4/4] Running FastAPI Backend Multilingual E2E tests...")
    client = httpx.Client(timeout=120.0)
    
    # Register & Login
    email = f"qa_tester_{random.randint(1000, 9999)}@example.com"
    reg_payload = {"name": "QA Tester", "email": email, "password": "Password123!"}
    
    try:
        r = client.post(f"{BACKEND_URL}/api/auth/register", json=reg_payload)
        if r.status_code not in (200, 201):
            return {"error": f"Registration failed: {r.status_code} - {r.text}"}
            
        r = client.post(f"{BACKEND_URL}/api/auth/login", json={"email": email, "password": reg_payload["password"]})
        if r.status_code != 200:
            return {"error": f"Login failed: {r.status_code} - {r.text}"}
    except Exception as e:
        return {"error": f"Auth setup exception: {str(e)}"}
        
    def stream_chat(messages, conversation_id=None):
        payload = {
            "messages": messages,
            "conversation_id": conversation_id,
            "language": "auto",
            "workspace_mode": "general",
            "temperature": 0.2
        }
        resp_text = ""
        conv_id = conversation_id
        
        try:
            with client.stream("POST", f"{BACKEND_URL}/api/chat/stream", json=payload) as r:
                if r.status_code != 200:
                    return f"HTTP {r.status_code}", None
                for line in r.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        event = json.loads(data_str)
                        if event.get("type") == "conversation_id":
                            conv_id = event.get("value")
                        elif event.get("type") == "text":
                            resp_text += event.get("value", "")
            return resp_text, conv_id
        except Exception as e:
            return f"Error: {str(e)}", None

    test_cases = [
        {"id": "TEST 1: English", "prompt": "What is the capital of India?", "expected_script": "English/Latin"},
        {"id": "TEST 2: Telugu", "prompt": "భారతదేశ రాజధాని ఏది?", "expected_script": "Telugu"},
        {"id": "TEST 3: Hindi", "prompt": "भारत की राजधानी क्या है?", "expected_script": "Hindi"},
        {"id": "TEST 4: Kannada", "prompt": "ಭಾರತದ ರಾಜಧಾನಿ ಯಾವುದು?", "expected_script": "Kannada"},
        {"id": "TEST 5: Tamil", "prompt": "இந்தியாவின் தலைநகரம் எது?", "expected_script": "Tamil"},
        {"id": "TEST 6: Mixed English + Telugu", "prompt": "India గురించి తెలుగులో చెప్పండి", "expected_script": "Telugu"},
    ]
    
    results = {}
    
    # Run tests 1 to 6
    for tc in test_cases:
        print(f"Running {tc['id']}...")
        ans, conv = stream_chat([{"role": "user", "content": tc["prompt"]}])
        detected = detect_script(ans)
        results[tc["id"]] = {
            "prompt": tc["prompt"],
            "response": ans,
            "detected_script": detected,
            "success": (detected == tc["expected_script"])
        }
        time.sleep(0.5)

    # Run TEST 7: Conversation switching
    print("Running TEST 7: Conversation switching...")
    ans_7a, conv_7 = stream_chat([{"role": "user", "content": "Tell me about India."}])
    time.sleep(0.5)
    
    messages_history = [
        {"role": "user", "content": "Tell me about India."},
        {"role": "assistant", "content": ans_7a},
        {"role": "user", "content": "ఇది తెలుగులో చెప్పండి."}
    ]
    ans_7b, _ = stream_chat(messages_history, conversation_id=conv_7)
    detected_7b = detect_script(ans_7b)
    
    results["TEST 7: Conv Switching Turn 1 (English)"] = {
        "prompt": "Tell me about India.",
        "response": ans_7a,
        "detected_script": detect_script(ans_7a),
        "success": (detect_script(ans_7a) == "English/Latin")
    }
    results["TEST 7: Conv Switching Turn 2 (Telugu)"] = {
        "prompt": "ఇది తెలుగులో చెప్పండి.",
        "response": ans_7b,
        "detected_script": detected_7b,
        "success": (detected_7b == "Telugu")
    }
    
    return results

def main():
    print("=================================================================")
    print("      NOVA AI MULTILINGUAL COMPREHENSIVE QA TEST RUNNER")
    print("=================================================================\n")
    
    ollama_ok, ollama_msg = test_ollama_status()
    print(f"Ollama Status: {'[PASS]' if ollama_ok else '[FAIL]'} - {ollama_msg}\n")
    
    direct_results = {}
    if ollama_ok:
        direct_results = test_ollama_direct()
        print("\nDirect Ollama Multilingual Check:")
        for lang, res in direct_results.items():
            print(f"  {lang}: {'[PASS]' if res['success'] else '[FAIL]'} (Detected script: {res['detected_script']})")
            print(f"    Response: {res['response']}")
            
    health_ok, ready_ok = test_backend_status()
    print(f"\nFastAPI Health check: {'[PASS]' if health_ok else '[FAIL]'}")
    print(f"FastAPI Readiness check: {'[PASS]' if ready_ok else '[FAIL]'}\n")
    
    backend_results = {}
    if health_ok:
        backend_results = test_backend_chat()
        if "error" in backend_results:
            print(f"Backend E2E chat run failed: {backend_results['error']}")
        else:
            print("\nBackend Chat Stream Multilingual Check:")
            for tc_id, res in backend_results.items():
                print(f"  {tc_id}: {'[PASS]' if res['success'] else '[FAIL]'} (Detected: {res['detected_script']})")
                print(f"    Prompt: {res['prompt']}")
                print(f"    Response: {res['response'][:100]}...")
                
    # Write full report to markdown file
    with open("multilingual_test_report.md", "w", encoding="utf-8") as f:
        f.write("# NOVA AI Multilingual QA Verification Report\n\n")
        
        f.write("## 1. System Components\n")
        f.write(f"- **Ollama Connection**: {'PASS' if ollama_ok else 'FAIL'} ({ollama_msg})\n")
        f.write(f"- **FastAPI Health Check**: {'PASS' if health_ok else 'FAIL'}\n")
        f.write(f"- **FastAPI Readiness Check**: {'PASS' if ready_ok else 'FAIL'}\n\n")
        
        if direct_results:
            f.write("## 2. Direct Ollama Model Tests\n")
            f.write("| Language | Query | Response | Detected Script | Result |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            prompts = {
                "Telugu": "భారతదేశ రాజధాని ఏది?",
                "Hindi": "भारत की राजधानी क्या है?",
                "Kannada": "ಭಾರತದ ರಾಜಧಾನಿ ಯಾವುದು?",
                "Tamil": "இந்தியாவின் தலைநகரம் எது?"
            }
            for lang, res in direct_results.items():
                f.write(f"| {lang} | {prompts[lang]} | {res['response']} | {res['detected_script']} | {'PASS' if res['success'] else 'FAIL'} |\n")
            f.write("\n")
            
        if backend_results and "error" not in backend_results:
            f.write("## 3. End-to-End FastAPI Chat Stream Tests\n")
            f.write("| Test Case | Prompt | Response | Detected Script | Result |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for tc_id, res in backend_results.items():
                clean_resp = res['response'].replace('\n', ' ')
                f.write(f"| {tc_id} | {res['prompt']} | {clean_resp} | {res['detected_script']} | {'PASS' if res['success'] else 'FAIL'} |\n")
            f.write("\n")
            
    print(f"\nWritten detailed report to: {os.path.abspath('multilingual_test_report.md')}")

if __name__ == "__main__":
    main()
