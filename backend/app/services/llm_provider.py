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

_shared_llm_client: Optional[httpx.AsyncClient] = None

def get_shared_llm_client() -> httpx.AsyncClient:
    global _shared_llm_client
    if _shared_llm_client is None or _shared_llm_client.is_closed:
        timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=15.0)
        limits = httpx.Limits(max_keepalive_connections=30, max_connections=50, keepalive_expiry=120.0)
        _shared_llm_client = httpx.AsyncClient(timeout=timeout, limits=limits)
    return _shared_llm_client

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
            if "openrouter.ai" in self.base_url or settings.LLM_PROVIDER == "openrouter":
                headers["HTTP-Referer"] = settings.FRONTEND_URL.split(",")[0]
                headers["X-Title"] = "NOVA AI"
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }

            import os
            max_tokens_val = os.getenv("MAX_GENERATION_TOKENS")
            if max_tokens_val:
                payload["max_tokens"] = int(max_tokens_val)

            # For local Ollama instances, keep the model loaded to prevent load latency on subsequent calls
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                payload["keep_alive"] = -1

            url = f"{self.base_url}/chat/completions"
            client = get_shared_llm_client()
            
            response = None
            success = False
            max_retries = settings.LLM_MAX_RETRIES

            for attempt in range(1, max_retries + 1):
                # Check circuit breaker for each retry attempt
                self.circuit_breaker.check_call()
                try:
                    prompt_len = sum(len(m.get("content", "")) for m in messages)
                    logger.info(
                        f"dispatch_request: provider=OpenAI-compatible, model={model}, "
                        f"prompt_length={prompt_len}, base_url={self.base_url}"
                    )
                    logger.info(f"DEBUG PAYLOAD: {[{'role': m.get('role'), 'len': len(m.get('content', '')), 'preview': m.get('content', '')[:60]} for m in messages]}")
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
                        raise AIProviderAuthError(err_msg)
                    elif response.status_code == 429:
                        if attempt == max_retries:
                            raise AIProviderRateLimitError(err_msg)
                    elif response.status_code in (500, 502, 503, 504):
                        if attempt == max_retries:
                            raise AIProviderUnavailableError(err_msg)
                    else:
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
            else:
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
    Raises a clear AIProviderNotConfiguredError when no AI provider key is configured.
    Never silently generates fake answers.
    """
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        raise AIProviderNotConfiguredError(
            "AI_PROVIDER_NOT_CONFIGURED: No AI provider is configured. Please set AI_API_KEY in backend/.env."
        )
        yield  # Make this an async generator

