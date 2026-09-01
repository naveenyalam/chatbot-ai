import httpx
import json

def run_language_test(lang_name, prompt):
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "stream": False
    }
    
    result_text = f"\n=== Testing {lang_name} ===\nPrompt: {prompt}\n"
    try:
        response = httpx.post(url, json=payload, timeout=60.0)
        if response.status_code == 200:
            result = response.json()
            result_text += f"Response: {result.get('response', '').strip()}\n"
        else:
            result_text += f"Error {response.status_code}: {response.text}\n"
    except Exception as e:
        result_text += f"Exception: {e}\n"
        
    with open("test_qwen_results.txt", "a", encoding="utf-8") as f:
        f.write(result_text)
    print(f"Done testing {lang_name}")

if __name__ == "__main__":
    # Clear file first
    with open("test_qwen_results.txt", "w", encoding="utf-8") as f:
        f.write("")
        
    tests = {
        "English": "What is artificial intelligence?",
        "Telugu": "కృత్రిమ మేధస్సు అంటే ఏమిటి?",
        "Hindi": "कृत्रिम बुद्धिमत्ता क्या है?",
        "Kannada": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಎಂದರೇನು?",
        "Tamil": "செயற்கை நுண்ணறிவு என்றால் என்ன?"
    }
    
    for lang, prompt in tests.items():
        run_language_test(lang, prompt)
