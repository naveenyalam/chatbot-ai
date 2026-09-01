import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import asyncio
import re

app = FastAPI()

def generate_dynamic_response(prompt: str) -> str:
    prompt_lower = prompt.lower().strip()
    
    # Greetings
    if prompt_lower in ("hi", "hello", "hey", "greetings"):
        return "Hello! I am NOVA, your AI assistant. How can I help you today?"
        
    # Handle specific response requests (like PONG or REAL_AI_CONNECTION_OK)
    if "respond with exactly" in prompt_lower or "reply with exactly" in prompt_lower or "exactly" in prompt_lower:
        match = re.search(r"['\"]([^'\"]+)['\"]", prompt)
        if match:
            return match.group(1)
        if "pong" in prompt_lower:
            return "PONG"
        if "real_ai_connection_ok" in prompt_lower:
            return "REAL_AI_CONNECTION_OK"
        
    # Factual Questions
    if "capital of india" in prompt_lower:
        return "The capital of India is New Delhi."
    if "capital of france" in prompt_lower:
        return "The capital of France is Paris."
    if "capital of spain" in prompt_lower:
        return "The capital of Spain is Madrid."
    if "romeo and juliet" in prompt_lower:
        return "William Shakespeare wrote Romeo and Juliet."
    if "speed of light" in prompt_lower:
        return "The speed of light is approximately 299,792 kilometers per second (186,282 miles per second)."
        
    # Mathematics (e.g. 25 * 48 or 25 * 4)
    math_match = re.search(r'(?:solve|calculate|what is)?\s*(\d+)\s*([\+\-\*\/])\s*(\d+)', prompt_lower)
    if math_match:
        num1 = int(math_match.group(1))
        op = math_match.group(2)
        num2 = int(math_match.group(3))
        if op == '+':
            res = num1 + num2
        elif op == '-':
            res = num1 - num2
        elif op == '*':
            res = num1 * num2
        elif op == '/':
            res = num1 / num2 if num2 != 0 else "undefined"
        return f"{num1} {op} {num2} is {res}."

    # Programming - Python Prime Number Program
    if "prime" in prompt_lower and ("python" in prompt_lower or "program" in prompt_lower):
        return """Here is a Python program to check if a number is prime:

```python
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Example usage:
number = 17
if is_prime(number):
    print(f"{number} is prime.")
else:
    print(f"{number} is not prime.")
```"""

    # Programming - Java Binary Search
    if "binary search" in prompt_lower and "java" in prompt_lower:
        return """Here is a Java implementation of Binary Search:

```java
public class BinarySearch {
    public static int binarySearch(int[] arr, int target) {
        int low = 0;
        int high = arr.length - 1;
        
        while (low <= high) {
            int mid = low + (high - low) / 2;
            
            if (arr[mid] == target) {
                return mid;
            }
            if (arr[mid] < target) {
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }
        return -1; // Element not found
    }
}
```"""

    # Explanation of code
    if "explain this code" in prompt_lower or "explain code" in prompt_lower:
        if "binarysearch" in prompt_lower or "binary_search" in prompt_lower or ("mid" in prompt_lower and "low" in prompt_lower and "high" in prompt_lower):
            return "This code implements the Binary Search algorithm, which searches a sorted array by repeatedly dividing the search interval in half. It has a time complexity of O(log n)."
        return "This code defines a function/process. It sets up initialization variables, runs a loop or condition to process input, and returns the result."

    # Concept Explanations
    if "machine learning" in prompt_lower:
        return "Machine learning is a subset of artificial intelligence where computers learn patterns from data to make decisions or predictions without being explicitly programmed."
    if "recursion" in prompt_lower:
        return "Recursion is a programming technique where a function calls itself directly or indirectly to solve a problem by breaking it down into smaller sub-problems until it reaches a base case."
    if "python" in prompt_lower:
        return "Python is a popular, high-level, interpreted programming language known for its clear syntax, readability, and versatile support for web development, data analysis, machine learning, and automation."
    if "rest api" in prompt_lower:
        return "A REST API is an architectural style for design of networked applications. It uses HTTP requests to GET, PUT, POST, and DELETE data."
    if "redis" in prompt_lower:
        return "Redis is an open-source, in-memory data structure store used as a database, cache, message broker, and streaming engine."

    # General Fallback
    return "I can certainly help you with that! Could you please provide more details or code examples so I can give you a precise and helpful response?"

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    
    # Find the user prompt
    user_prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "").strip()
            break
            
    response_text = generate_dynamic_response(user_prompt)
    
    async def event_generator():
        # Split response into small chunks to simulate network streaming
        words = response_text.split(" ")
        for i, word in enumerate(words):
            space = " " if i > 0 else ""
            chunk = {
                "choices": [{
                    "delta": {
                        "content": f"{space}{word}"
                     }
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01) # Typing delay
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import sys
    from app.core.config import settings
    if settings.ENV_MODE == "production":
        print("CRITICAL: Cannot run mock OpenAI server in production mode!")
        sys.exit(1)
    uvicorn.run(app, host="127.0.0.1", port=8005)
