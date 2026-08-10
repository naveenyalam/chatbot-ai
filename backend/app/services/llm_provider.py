import abc
import json
import logging
import asyncio
import random
from typing import AsyncGenerator, List, Dict
import httpx
from app.core.config import settings
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

logger = logging.getLogger("nova-ai.llm-provider")

class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM tokens asynchronously chunk by chunk.
        """
        pass

class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.circuit_breaker = CircuitBreaker("openai")

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        from app.core.concurrency import operation_limit
        async with operation_limit("llm"):
            # Check circuit breaker before proceeding
            self.circuit_breaker.check_call()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }

            url = f"{self.base_url}/chat/completions"
            timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=8.0)
            client = httpx.AsyncClient(timeout=timeout)
            
            response = None
            success = False
            max_retries = settings.LLM_MAX_RETRIES

            for attempt in range(1, max_retries + 1):
                # Check circuit breaker for each retry attempt
                self.circuit_breaker.check_call()
                try:
                    logger.info(f"Dispatching POST request to {url} with model {model} (Attempt {attempt}/{max_retries})")
                    response = await client.send(
                        client.build_request("POST", url, headers=headers, json=payload),
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        self.circuit_breaker.record_success()
                        success = True
                        break
                    
                    # Non-200 responses
                    err_bytes = await response.aread()
                    err_msg = err_bytes.decode(errors="ignore")
                    logger.error(f"LLM API returned error status {response.status_code}: {err_msg}")
                    
                    # Record error metric
                    from app.core.metrics import LLM_PROVIDER_ERRORS_TOTAL
                    LLM_PROVIDER_ERRORS_TOTAL.labels(provider="openai", model=model, status_code=str(response.status_code)).inc()
                    
                    self.circuit_breaker.record_failure()
                    
                    # Retry only on 429 and 5xx errors
                    if response.status_code in (401, 403):
                        await client.aclose()
                        raise AIProviderAuthError(err_msg)
                    elif response.status_code == 429:
                        if attempt == max_retries:
                            await client.aclose()
                            raise AIProviderRateLimitError(err_msg)
                    elif response.status_code in (500, 502, 503, 504):
                        if attempt == max_retries:
                            await client.aclose()
                            raise AIProviderUnavailableError(err_msg)
                    else:
                        await client.aclose()
                        raise AIServiceError(f"AI Provider returned HTTP {response.status_code}: {err_msg}")
                        
                except (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError, asyncio.TimeoutError) as exc:
                    logger.warning(f"Transient HTTP error on attempt {attempt}: {exc}")
                    self.circuit_breaker.record_failure()
                    
                    from app.core.metrics import LLM_RETRY_TOTAL, LLM_TIMEOUT_TOTAL
                    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectTimeout, asyncio.TimeoutError)):
                        LLM_TIMEOUT_TOTAL.labels(provider="openai", model=model).inc()
                        error_type = "timeout"
                    else:
                        error_type = "network_error"
                    LLM_RETRY_TOTAL.labels(provider="openai", model=model, error_type=error_type).inc()
                    
                    if attempt == max_retries:
                        await client.aclose()
                        raise AIProviderUnavailableError(f"AI Provider endpoint is unreachable: {exc}") from exc
                
                # Backoff delay with jitter
                delay = min(10.0, 1.0 * (2 ** (attempt - 1)) + random.uniform(0, 0.5))
                await asyncio.sleep(delay)

            if success and response:
                try:
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                choices = chunk_json.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                pass
                finally:
                    await response.aclose()
                    await client.aclose()
            else:
                await client.aclose()
                raise RuntimeError("Failed to establish stream connection with AI Provider.")


class MockLLMProvider(BaseLLMProvider):
    """
    Mock Provider — FOR AUTOMATED TESTS ONLY.
    This class MUST NOT be used in production or as a silent fallback.
    In production, raise a clear error if no AI_API_KEY is set.
    """
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        logger.warning("MockLLMProvider invoked — this should only happen in automated tests.")
        # Yield nothing; tests can subclass or patch as needed.
        return
        yield  # make this an async generator


from app.core.errors import AIProviderNotConfiguredError, AIProviderAuthError, AIProviderUnavailableError, AIProviderRateLimitError

class NotConfiguredProvider(BaseLLMProvider):
    """
    Yields helpful setup instructions when no AI provider key is configured.
    """
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        user_msg = messages[-1]["content"] if messages else ""
        guide = (
            f"Hello! I received your message: **\"{user_msg}\"**\n\n"
            "⚠️ **AI Provider Key Required**:\n"
            "The backend is currently running without an `AI_API_KEY` configured in `backend/.env`.\n\n"
            "### How to enable real AI responses:\n"
            "1. Open `backend/.env` in your project workspace.\n"
            "2. Add your API key: `AI_API_KEY=your_openai_or_groq_api_key`\n"
            "3. Save the file and restart the backend!\n\n"
            "*Note: For automated offline testing, set `AI_USE_MOCK=true` in `backend/.env`.*"
        )
        for chunk in guide.split(" "):
            yield chunk + " "

