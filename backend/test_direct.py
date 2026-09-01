import httpx
import json

payload = {
    'model': 'llama3.2:1b',
    'messages': [
        {'role': 'system', 'content': 'You MUST respond ONLY in Telugu script. Do not write in English.'},
        {'role': 'user', 'content': 'Tell me about India.'},
        {'role': 'assistant', 'content': 'India is a country in South Asia.'},
        {'role': 'user', 'content': 'ఇది తెలుగులో చెప్పండి.'}
    ],
    'stream': False
}

r = httpx.post('http://127.0.0.1:11434/v1/chat/completions', json=payload, timeout=60.0)
content = r.json()['choices'][0]['message']['content']

with open('test_direct_results.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved output to test_direct_results.txt")
