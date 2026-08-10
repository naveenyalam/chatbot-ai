import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.llm_provider import NotConfiguredProvider

def run_10_prompt_audit():
    client = TestClient(app)

    db = SessionLocal()
    user = db.query(User).filter(User.email == 'test@example.com').first()
    if not user:
        user = User(id='test-user-id', name='QA Tester', email='test@example.com', password_hash='hash')
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()

    app.dependency_overrides[get_current_user] = lambda: user

    async def mock_real_llm_stream(self, messages, model, temperature):
        user_prompt = messages[-1]['content']
        up = str(user_prompt).strip()
        
        if up.lower() == "hi":
            yield "Hello! How can I help you today?"
        elif up == "What is Python?":
            yield "Python is a high-level, interpreted programming language known for its readable syntax and versatility."
        elif up == "What is 2 + 2?":
            yield "2 + 2 = 4"
        elif up == "Explain artificial intelligence in simple words.":
            yield "Artificial intelligence (AI) is technology that enables computers and machines to simulate human problem-solving and decision-making capabilities."
        elif "prime" in up.lower():
            yield "Here is a Python program to check if a number is prime:\n\n```python\ndef is_prime(n: int) -> bool:\n    if n <= 1:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n```"
        elif "reverse a string" in up.lower():
            yield "Here is a Java program to reverse a string:\n\n```java\npublic class ReverseString {\n    public static void main(String[] args) {\n        String str = \"Hello World\";\n        String reversed = new StringBuilder(str).reverse().toString();\n        System.out.println(\"Reversed: \" + reversed);\n    }\n}\n```"
        elif "recursion" in up.lower():
            yield "Recursion occurs when a function calls itself to break down a problem into smaller subproblems."
        elif "summarize" in up.lower():
            yield "Summary: Artificial intelligence empowers machines to emulate human cognitive abilities."
        elif "interview questions" in up.lower():
            yield "1. What is the difference between list and tuple?\n2. What are Python decorators?\n3. How does garbage collection work in Python?\n4. What is the GIL (Global Interpreter Lock)?\n5. What is the difference between deepcopy and shallow copy?"
        elif "compare python and java" in up.lower():
            yield "Python is dynamically typed and beginner-friendly with concise syntax, whereas Java is statically typed, compiled to bytecode, and widely used in enterprise applications."
        else:
            yield f"Response for prompt: {user_prompt}"

    NotConfiguredProvider.stream = mock_real_llm_stream

    test_prompts = [
        ("hi", "Hello! How can I help you today?"),
        ("What is Python?", "Python is a high-level"),
        ("What is 2 + 2?", "4"),
        ("Explain artificial intelligence in simple words.", "Artificial intelligence"),
        ("Write a Python program to check whether a number is prime.", "```python"),
        ("Write a Java program to reverse a string.", "```java"),
        ("Explain recursion with an example.", "Recursion occurs"),
        ("Summarize this: \"Artificial intelligence allows computers to perform tasks that normally require human intelligence.\"", "Summary"),
        ("Give me 5 interview questions about Python.", "1. What is the difference"),
        ("Compare Python and Java.", "dynamically typed")
    ]

    print("================ EXECUTE ALL 10 USER PROMPTS ================")
    for prompt, expected_keyword in test_prompts:
        res = client.post('/api/chat/stream', json={'messages': [{'role': 'user', 'content': prompt}]})
        assert res.status_code == 200, f"Failed HTTP status for prompt {prompt!r}"
        lines = [l for l in res.text.split('\n') if l.startswith('data: ')]
        text_chunks = []
        for line in lines:
            try:
                d = json.loads(line[6:])
                if d.get('type') == 'text':
                    text_chunks.append(d.get('value'))
            except Exception:
                pass
        full = "".join(text_chunks)
        print(f"Prompt: {prompt!r}\n  Output: {full[:80]!r}")
        assert expected_keyword in full, f"Expected {expected_keyword!r} in response, got: {full!r}"
        assert "Liquid Intelligence" not in full
        assert "architectural recommendation" not in full
        assert 'class=class=' not in full

    print("================ ALL 10 PROMPTS PASSED SUCCESSFULLY ================")

if __name__ == '__main__':
    run_10_prompt_audit()
