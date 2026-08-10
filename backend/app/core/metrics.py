from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "nova_http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "nova_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# AI / LLM metrics
LLM_REQUESTS_TOTAL = Counter(
    "nova_llm_requests_total",
    "Total count of LLM requests",
    ["provider", "model", "status"]
)

LLM_REQUEST_DURATION = Histogram(
    "nova_llm_request_duration_seconds",
    "LLM requests execution latency in seconds",
    ["provider", "model"]
)

LLM_FALLBACKS_TOTAL = Counter(
    "nova_llm_fallbacks_total",
    "Total count of LLM provider failover activations",
    ["original_provider", "fallback_provider"]
)

# Agent metrics
AGENT_RUNS_TOTAL = Counter(
    "nova_agent_runs_total",
    "Total count of agent runs",
    ["agent_type", "status"]
)

AGENT_RUN_DURATION = Histogram(
    "nova_agent_run_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type"]
)

TOOL_CALLS_TOTAL = Counter(
    "nova_tool_calls_total",
    "Total count of agent tool executions",
    ["tool_name", "status"]
)

# RAG metrics
RAG_SEARCHES_TOTAL = Counter(
    "nova_rag_searches_total",
    "Total count of RAG retrieval database searches",
    ["status"]
)

RAG_SEARCH_DURATION = Histogram(
    "nova_rag_search_duration_seconds",
    "RAG search and embedding generation latency in seconds"
)

# Infrastructure metrics
REDIS_OPS_TOTAL = Counter(
    "nova_redis_operations_total",
    "Total count of Redis database operations",
    ["op_type", "status"]
)

DB_OPS_TOTAL = Counter(
    "nova_db_operations_total",
    "Total count of SQL Database operations",
    ["op_type", "status"]
)

REDIS_CACHE_HITS_TOTAL = Counter(
    "nova_redis_cache_hits_total",
    "Total count of Redis cache hits"
)

REDIS_CACHE_MISSES_TOTAL = Counter(
    "nova_redis_cache_misses_total",
    "Total count of Redis cache misses"
)

# Phase 8.5 metrics
LLM_RETRY_TOTAL = Counter(
    "nova_llm_retry_total",
    "Total count of LLM provider retries",
    ["provider", "model", "error_type"]
)

LLM_TIMEOUT_TOTAL = Counter(
    "nova_llm_timeout_total",
    "Total count of LLM request timeouts",
    ["provider", "model"]
)

LLM_FALLBACK_TOTAL = Counter(
    "nova_llm_fallback_total",
    "Total count of LLM provider fallback attempts",
    ["original_provider", "fallback_provider"]
)

LLM_PROVIDER_ERRORS_TOTAL = Counter(
    "nova_llm_provider_errors_total",
    "Total count of LLM provider HTTP errors",
    ["provider", "model", "status_code"]
)

RAG_CACHE_HIT_TOTAL = Counter(
    "nova_rag_cache_hit_total",
    "Total count of RAG retrieval cache hits"
)

RAG_CACHE_MISS_TOTAL = Counter(
    "nova_rag_cache_miss_total",
    "Total count of RAG retrieval cache misses"
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "nova_rag_retrieval_latency",
    "RAG query retrieval latency in seconds"
)

RAG_CHUNKS_RETURNED = Counter(
    "nova_rag_chunks_returned",
    "Total count of document chunks returned"
)

RAG_CONTEXT_SIZE = Counter(
    "nova_rag_context_size_chars",
    "Total count of characters sent as RAG context"
)

AGENT_TIMEOUT_TOTAL = Counter(
    "nova_agent_timeout_total",
    "Total count of agent runs that timed out",
    ["agent_type"]
)

AGENT_CANCELLED_TOTAL = Counter(
    "nova_agent_cancelled_total",
    "Total count of agent runs that were cancelled",
    ["agent_type"]
)

AGENT_LIMIT_EXCEEDED_TOTAL = Counter(
    "nova_agent_limit_exceeded_total",
    "Total count of agent runs that exceeded limit caps",
    ["agent_type"]
)

# Phase 12 Performance & Token Cost metrics
LLM_INPUT_TOKENS_TOTAL = Counter(
    "nova_llm_input_tokens_total",
    "Total count of input tokens sent to LLM providers",
    ["provider", "model"]
)

LLM_OUTPUT_TOKENS_TOTAL = Counter(
    "nova_llm_output_tokens_total",
    "Total count of output tokens received from LLM providers",
    ["provider", "model"]
)

LLM_ESTIMATED_COST_DOLLARS_TOTAL = Counter(
    "nova_llm_estimated_cost_dollars_total",
    "Estimated total cost in USD for LLM API calls",
    ["provider", "model"]
)

RAG_EMPTY_RETRIEVALS_TOTAL = Counter(
    "nova_rag_empty_retrievals_total",
    "Total count of RAG retrieval queries yielding zero chunks"
)

SSE_FIRST_TOKEN_LATENCY = Histogram(
    "nova_sse_first_token_latency_seconds",
    "Time-to-first-token latency for SSE streaming requests in seconds"
)

# Phase 13 Distributed Observability & Autonomous Operations metrics
ACTIVE_HTTP_REQUESTS = Gauge(
    "nova_active_http_requests",
    "Current number of concurrently executing HTTP requests"
)

ACTIVE_SSE_STREAMS = Gauge(
    "nova_active_sse_streams",
    "Current number of active client SSE stream connections"
)

DB_POOL_UTILIZATION = Gauge(
    "nova_db_pool_utilization_ratio",
    "Ratio of active PostgreSQL connections to total pool limit"
)

REDIS_OPERATION_LATENCY = Histogram(
    "nova_redis_operation_latency_seconds",
    "Redis command execution latency in seconds",
    ["op_type"]
)

CIRCUIT_BREAKER_STATE_GAUGE = Gauge(
    "nova_circuit_breaker_state",
    "Circuit breaker status code (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
    ["provider"]
)

SECURITY_VIOLATIONS_TOTAL = Counter(
    "nova_security_violations_total",
    "Total count of detected security anomaly violations",
    ["violation_type"]
)

AI_QUALITY_GROUNDING_SCORE = Histogram(
    "nova_ai_quality_grounding_score",
    "Grounding score evaluation distribution (0.0 to 1.0)"
)


