import httpx
import json
import random
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_qa():
    client = httpx.Client(timeout=180.0)
    
    # 1. Register test user
    email = f"final_qa_{random.randint(10000, 99999)}@example.com"
    reg_payload = {
        "name": "Final QA Tester",
        "email": email,
        "password": "Password123!"
    }
    
    print("=== STEP 1: REGISTRATION ===")
    res = client.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if res.status_code not in (200, 201):
        print(f"Registration failed: {res.status_code} - {res.text}")
        sys.exit(1)
    print(f"Registered user: {email}")

    # 2. Login
    print("\n=== STEP 2: LOGIN ===")
    login_payload = {"email": email, "password": reg_payload["password"]}
    res = client.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"Login failed: {res.status_code} - {res.text}")
        sys.exit(1)
    print("Logged in successfully.")

    # Helper to stream chat responses
    def ask_nova(messages, conversation_id=None, language="auto", temperature=0.2):
        payload = {
            "messages": messages,
            "conversation_id": conversation_id,
            "language": language,
            "workspace_mode": "general",
            "temperature": temperature
        }
        
        response_text = ""
        conv_id = conversation_id
        
        with client.stream("POST", f"{BASE_URL}/api/chat/stream", json=payload, timeout=300.0) as r:
            if r.status_code != 200:
                print(f"Error: HTTP {r.status_code}")
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
                    except Exception:
                        pass
        print()
        return response_text, conv_id

    qa_report = {}

    # ==================================================
    # 4. RESPONSE QUALITY TESTS
    # ==================================================
    print("\n=== VERIFYING RESPONSE QUALITY ===")
    
    # English
    print("\n[PROMPT: English AI Description]")
    ans_en, _ = ask_nova([{"role": "user", "content": "Explain Artificial Intelligence to a beginner with a real-world example."}])
    qa_report["English quality"] = "PASS" if len(ans_en) > 50 else "FAIL"

    # Telugu
    print("\n[PROMPT: Telugu AI Description]")
    ans_te, _ = ask_nova([{"role": "user", "content": "కృత్రిమ మేధస్సు అంటే ఏమిటి? ఒక సాధారణ ఉదాహరణతో తెలుగులో వివరించండి."}])
    # Check for Telugu characters range (0x0C00 to 0x0C7F)
    has_te_chars = bool(re.search(r'[\u0c00-\u0c7f]', ans_te))
    qa_report["Telugu quality"] = "PASS" if has_te_chars else "FAIL"

    # Hindi
    print("\n[PROMPT: Hindi AI Description]")
    ans_hi, _ = ask_nova([{"role": "user", "content": "आर्टिफिशियल इंटेलिजेंस क्या है? एक सरल उदाहरण के साथ हिंदी में समझाइए।"}])
    # Check for Devanagari range (0x0900 to 0x097F)
    has_hi_chars = bool(re.search(r'[\u0900-\u097f]', ans_hi))
    qa_report["Hindi quality"] = "PASS" if has_hi_chars else "FAIL"

    # Kannada
    print("\n[PROMPT: Kannada AI Description]")
    ans_kn, _ = ask_nova([{"role": "user", "content": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಎಂದರೇನು? ಸರಳ ಉದಾಹರಣೆಯೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲಿ ವಿವರಿಸಿ."}])
    # Check for Kannada range (0x0C80 to 0x0CFF)
    has_kn_chars = bool(re.search(r'[\u0c80-\u0cff]', ans_kn))
    qa_report["Kannada quality"] = "PASS" if has_kn_chars else "FAIL"

    # Tamil
    print("\n[PROMPT: Tamil AI Description]")
    ans_ta, _ = ask_nova([{"role": "user", "content": "செயற்கை நுண்ணறிவு என்றால் என்ன? ஒரு எளிய உதாரணத்துடன் தமிழில் விளக்குங்கள்."}])
    # Check for Tamil range (0x0B80 to 0x0BFF)
    has_ta_chars = bool(re.search(r'[\u0b80-\u0bff]', ans_ta))
    qa_report["Tamil quality"] = "PASS" if has_ta_chars else "FAIL"

    # ==================================================
    # 5. TECHNICAL TESTS
    # ==================================================
    print("\n=== VERIFYING TECHNICAL TOPICS ===")
    
    # Python code
    print("\n[PROMPT: Python Prime Checker]")
    ans_code, _ = ask_nova([{"role": "user", "content": "Give me a Python program to check whether a number is prime. Explain the code."}])
    has_python_block = "```python" in ans_code or "def is_prime" in ans_code
    qa_report["Programming"] = "PASS" if has_python_block else "FAIL"

    # Telugu Roadmap
    print("\n[PROMPT: Telugu Python Roadmap]")
    ans_roadmap_te, _ = ask_nova([{"role": "user", "content": "తెలుగులో Python నేర్చుకోవడానికి beginner roadmap ఇవ్వండి."}])
    
    # Hindi ML Roadmap
    print("\n[PROMPT: Hindi ML Roadmap]")
    ans_roadmap_hi, _ = ask_nova([{"role": "user", "content": "हिंदी में Machine Learning का beginner roadmap दीजिए।"}])

    # Kannada IoT Roadmap
    print("\n[PROMPT: Kannada IoT roadmap]")
    ans_roadmap_kn, _ = ask_nova([{"role": "user", "content": "ಕನ್ನಡದಲ್ಲಿ IoT ಎಂದರೇನು ಮತ್ತು ಅದನ್ನು ಹೇಗೆ ಕಲಿಯಬೇಕು ಎಂದು ವಿವರಿಸಿ."}])

    # Tamil AI Roadmap
    print("\n[PROMPT: Tamil AI Roadmap]")
    ans_roadmap_ta, _ = ask_nova([{"role": "user", "content": "தமிழில் AI கற்க ஒரு beginner roadmap கொடுக்கவும்."}])

    # ==================================================
    # 6. MATHEMATICS TEST
    # ==================================================
    print("\n=== VERIFYING MATHEMATICS ===")
    print("\n[PROMPT: 25 × 48]")
    ans_math, _ = ask_nova([{"role": "user", "content": "Calculate 25 × 48 and explain the calculation."}])
    has_correct_result = "1200" in ans_math
    qa_report["Mathematics"] = "PASS" if has_correct_result else "FAIL"

    # ==================================================
    # 7. MEMORY TEST
    # ==================================================
    print("\n=== VERIFYING MEMORY ===")
    print("\n[Turn 1: Setting Name & Language]")
    ans_mem1, conv_mem = ask_nova([{"role": "user", "content": "నా పేరు రవి. నేను Python నేర్చుకుంటున్నాను."}])
    
    print("\n[Turn 2: Asking recall]")
    history_mem = [
        {"role": "user", "content": "నా పేరు రవి. నేను Python నేర్చుకుంటున్నాను."},
        {"role": "assistant", "content": ans_mem1},
        {"role": "user", "content": "నా పేరు ఏమిటి? నేను ఏమి నేర్చుకుంటున్నాను?"}
    ]
    ans_mem2, _ = ask_nova(history_mem, conversation_id=conv_mem)
    recalls_ravi = "రవి" in ans_mem2 or "Ravi" in ans_mem2
    recalls_python = "Python" in ans_mem2 or "python" in ans_mem2
    qa_report["Memory"] = "PASS" if (recalls_ravi and recalls_python) else "FAIL"

    # ==================================================
    # 8. LANGUAGE SWITCHING
    # ==================================================
    print("\n=== VERIFYING LANGUAGE SWITCHING ===")
    
    # 8.1 English
    print("\n[Turn 1: English Python]")
    ans_sw1, conv_sw = ask_nova([{"role": "user", "content": "Explain Python in English."}])
    
    # 8.2 Telugu
    print("\n[Turn 2: Telugu Python]")
    hist_sw = [{"role": "user", "content": "Explain Python in English."}, {"role": "assistant", "content": ans_sw1},
               {"role": "user", "content": "ఇప్పుడు Python గురించి తెలుగులో వివరించండి."}]
    ans_sw2, _ = ask_nova(hist_sw, conversation_id=conv_sw)
    
    # 8.3 Hindi
    print("\n[Turn 3: Hindi Python]")
    hist_sw.append({"role": "assistant", "content": ans_sw2})
    hist_sw.append({"role": "user", "content": "अब Python के बारे में हिंदी में बताइए।"})
    ans_sw3, _ = ask_nova(hist_sw, conversation_id=conv_sw)
    
    # 8.4 Kannada
    print("\n[Turn 4: Kannada Python]")
    hist_sw.append({"role": "assistant", "content": ans_sw3})
    hist_sw.append({"role": "user", "content": "Python ಬಗ್ಗೆ ಕನ್ನಡದಲ್ಲಿ ವಿವರಿಸಿ."})
    ans_sw4, _ = ask_nova(hist_sw, conversation_id=conv_sw)

    # 8.5 Tamil
    print("\n[Turn 5: Tamil Python]")
    hist_sw.append({"role": "assistant", "content": ans_sw4})
    hist_sw.append({"role": "user", "content": "Python பற்றி தமிழில் விளக்குங்கள்."})
    ans_sw5, _ = ask_nova(hist_sw, conversation_id=conv_sw)

    has_te = bool(re.search(r'[\u0c00-\u0c7f]', ans_sw2))
    has_hi = bool(re.search(r'[\u0900-\u097f]', ans_sw3))
    has_kn = bool(re.search(r'[\u0c80-\u0cff]', ans_sw4))
    has_ta = bool(re.search(r'[\u0b80-\u0bff]', ans_sw5))
    qa_report["Language switching"] = "PASS" if (has_te and has_hi and has_kn and has_ta) else "FAIL"

    # ==================================================
    # 9. MIXED LANGUAGE
    # ==================================================
    print("\n=== VERIFYING MIXED LANGUAGE ===")
    
    print("\n[Prompt 1: Python అంటే ఏమిటి? Explain simply in Telugu.]")
    ans_mix1, _ = ask_nova([{"role": "user", "content": "Python అంటే ఏమిటి? Explain it simply in Telugu."}])
    
    print("\n[Prompt 2: AI क्या है? Explain with an example in Hindi.]")
    ans_mix2, _ = ask_nova([{"role": "user", "content": "AI क्या है? Explain with an example in Hindi."}])

    print("\n[Prompt 3: IoT ಎಂದರೇನು? Explain simply in Kannada.]")
    ans_mix3, _ = ask_nova([{"role": "user", "content": "IoT ಎಂದರೇನು? Explain simply in Kannada."}])

    print("\n[Prompt 4: Machine Learning என்றால் என்ன? Explain simply in Tamil.]")
    ans_mix4, _ = ask_nova([{"role": "user", "content": "Machine Learning என்றால் என்ன? Explain simply in Tamil."}])

    has_mix1 = bool(re.search(r'[\u0c00-\u0c7f]', ans_mix1))
    has_mix2 = bool(re.search(r'[\u0900-\u097f]', ans_mix2))
    has_mix3 = bool(re.search(r'[\u0c80-\u0cff]', ans_mix3))
    has_mix4 = bool(re.search(r'[\u0b80-\u0bff]', ans_mix4))
    qa_report["Mixed language"] = "PASS" if (has_mix1 and has_mix2 and has_mix3 and has_mix4) else "FAIL"

    # Write report summary
    print("\n=== QA REPORT SUMMARY ===")
    for k, v in qa_report.items():
        print(f"  {k}: {v}")
        
    with open("verify_final_qa_results.json", "w") as rf:
        json.dump(qa_report, rf, indent=2)

if __name__ == "__main__":
    run_qa()
