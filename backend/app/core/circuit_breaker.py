import time
import logging
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger("nova-ai.circuit-breaker")

class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is OPEN or HALF_OPEN-saturated."""
    pass

class CircuitBreaker:
    """
    Stateful circuit breaker mapping to 'CLOSED', 'OPEN', 'HALF_OPEN'.
    Uses Redis when available, falling back to local memory dicts otherwise.
    """
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.threshold = settings.LLM_CIRCUIT_FAILURE_THRESHOLD
        self.cooldown = settings.LLM_CIRCUIT_COOLDOWN_SECONDS
        
        # Local in-memory state fallback
        self._local_state = "CLOSED"
        self._local_failures = 0
        self._local_last_failure_time = 0.0
        self._local_half_open_probes = 0

    def _get_redis_keys(self):
        prefix = f"nova:circuit:{self.provider_name}"
        return {
            "state": f"{prefix}:state",
            "failures": f"{prefix}:failures",
            "last_failure": f"{prefix}:last_failure",
            "probes": f"{prefix}:probes"
        }

    def get_state(self) -> str:
        redis_client = get_redis_client()
        if not redis_client:
            # Fallback to local state
            if self._local_state == "OPEN":
                if time.time() - self._local_last_failure_time > self.cooldown:
                    logger.info(f"CircuitBreaker [{self.provider_name}]: Cooldown elapsed. Changing from OPEN to HALF_OPEN.")
                    self._local_state = "HALF_OPEN"
                    self._local_half_open_probes = 0
            return self._local_state

        keys = self._get_redis_keys()
        state = redis_client.get(keys["state"]) or "CLOSED"
        
        if state == "OPEN":
            last_fail = redis_client.get(keys["last_failure"])
            if last_fail:
                elapsed = time.time() - float(last_fail)
                if elapsed > self.cooldown:
                    logger.info(f"CircuitBreaker [{self.provider_name}]: Cooldown elapsed. Changing from OPEN to HALF_OPEN.")
                    redis_client.set(keys["state"], "HALF_OPEN")
                    redis_client.set(keys["probes"], 0)
                    state = "HALF_OPEN"
        return state

    def check_call(self):
        state = self.get_state()
        if state == "OPEN":
            raise CircuitBreakerOpenException(f"Circuit breaker for provider '{self.provider_name}' is OPEN.")
        
        if state == "HALF_OPEN":
            # Allow limited half-open probe requests (e.g. only 1 probe at a time)
            redis_client = get_redis_client()
            if redis_client:
                keys = self._get_redis_keys()
                probes = redis_client.incr(keys["probes"])
                if probes > 1:
                    raise CircuitBreakerOpenException(f"Circuit breaker for provider '{self.provider_name}' is HALF_OPEN (probe in progress).")
            else:
                self._local_half_open_probes += 1
                if self._local_half_open_probes > 1:
                    raise CircuitBreakerOpenException(f"Circuit breaker for provider '{self.provider_name}' is HALF_OPEN (probe in progress).")

    def record_success(self):
        redis_client = get_redis_client()
        if not redis_client:
            if self._local_state == "HALF_OPEN":
                logger.info(f"CircuitBreaker [{self.provider_name}]: Probe success. Closing circuit.")
            self._local_state = "CLOSED"
            self._local_failures = 0
            self._local_half_open_probes = 0
            return

        keys = self._get_redis_keys()
        state = redis_client.get(keys["state"]) or "CLOSED"
        if state == "HALF_OPEN":
            logger.info(f"CircuitBreaker [{self.provider_name}]: Probe success. Closing circuit.")
        redis_client.set(keys["state"], "CLOSED")
        redis_client.delete(keys["failures"])
        redis_client.delete(keys["probes"])

    def record_failure(self):
        redis_client = get_redis_client()
        now = time.time()
        if not redis_client:
            self._local_failures += 1
            self._local_last_failure_time = now
            state = self._local_state
            if state in ("CLOSED", "HALF_OPEN"):
                if self._local_failures >= self.threshold or state == "HALF_OPEN":
                    logger.warning(f"CircuitBreaker [{self.provider_name}]: Trip threshold reached. Opening circuit.")
                    self._local_state = "OPEN"
            return

        keys = self._get_redis_keys()
        state = redis_client.get(keys["state"]) or "CLOSED"
        failures = redis_client.incr(keys["failures"])
        redis_client.set(keys["last_failure"], str(now))
        
        # Set expire on failures/last_failure to avoid junk keys
        redis_client.expire(keys["failures"], self.cooldown * 2)
        redis_client.expire(keys["last_failure"], self.cooldown * 2)

        if state in ("CLOSED", "HALF_OPEN"):
            if failures >= self.threshold or state == "HALF_OPEN":
                logger.warning(f"CircuitBreaker [{self.provider_name}]: Trip threshold reached/probe failed. Opening circuit.")
                redis_client.set(keys["state"], "OPEN")
                redis_client.expire(keys["state"], self.cooldown)
