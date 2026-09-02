import os
from typing import List
from pydantic_core import PydanticCustomError
from pydantic import BaseModel, field_validator, model_validator
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class Settings(BaseModel):
    # Security and Environment Settings
    ENV_MODE: str = os.getenv("ENV_MODE", "development")
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    MAX_JSON_REQUEST_SIZE: int = int(os.getenv("MAX_JSON_REQUEST_SIZE", "1048576")) # default 1MB
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "20000"))
    MAX_FILES_PER_REQUEST: int = int(os.getenv("MAX_FILES_PER_REQUEST", "10"))
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # AI Provider Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    CLOUD_LLM_API_KEY: str | None = os.getenv("CLOUD_LLM_API_KEY") or None
    AI_API_KEY: str | None = os.getenv("CLOUD_LLM_API_KEY") or os.getenv("AI_API_KEY") or None  # treat empty string as None
    AI_MODEL: str = os.getenv("AI_MODEL", "qwen2.5:3b" if os.getenv("LLM_PROVIDER", "ollama").lower() == "ollama" else "gpt-4o-mini")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "http://127.0.0.1:11434/v1" if os.getenv("LLM_PROVIDER", "ollama").lower() == "ollama" else "https://api.openai.com/v1")
    AI_USE_MOCK: bool = os.getenv("AI_USE_MOCK", "false").lower() == "true"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://nova-ai-chat-pi.vercel.app,http://localhost:3000,http://localhost:3001")

    # Database and Authentication Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nova_ai.db")
    REDIS_URL: str | None = os.getenv("REDIS_URL")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "nova-premium-secret-token-key-change-in-prod-11223344")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Web Search Settings
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "mock")
    SEARCH_API_KEY: str | None = os.getenv("SEARCH_API_KEY")
    SEARCH_MAX_RESULTS: int = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))

    # Deep Research Settings
    RESEARCH_MAX_STEPS: int = int(os.getenv("RESEARCH_MAX_STEPS", "5"))
    RESEARCH_MAX_SEARCHES: int = int(os.getenv("RESEARCH_MAX_SEARCHES", "8"))
    RESEARCH_MAX_SOURCES: int = int(os.getenv("RESEARCH_MAX_SOURCES", "20"))

    # Multimodal Vision Settings
    VISION_MODEL: str = os.getenv("VISION_MODEL", "gpt-4o-mini")
    VISION_MAX_IMAGE_SIZE_MB: int = int(os.getenv("VISION_MAX_IMAGE_SIZE_MB", "10"))

    # AI Image Generation Settings
    IMAGE_GENERATION_ENABLED: bool = os.getenv("IMAGE_GENERATION_ENABLED", "true").lower() == "true"
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "openai").lower()
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "dall-e-3")
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_SIZE: str = os.getenv("IMAGE_SIZE", "1024x1024")
    IMAGE_GENERATION_RATE_LIMIT: int = int(os.getenv("IMAGE_GENERATION_RATE_LIMIT", "10"))
    IMAGE_GENERATION_MAX_PROMPT_LENGTH: int = int(os.getenv("IMAGE_GENERATION_MAX_PROMPT_LENGTH", "1000"))
    IMAGE_STORAGE_PROVIDER: str = os.getenv("IMAGE_STORAGE_PROVIDER", "url")

    # Model Routing Strategy
    AI_FAST_MODEL: str = os.getenv("AI_FAST_MODEL", "gpt-4o-mini")
    FAST_CHAT_MODEL: str = os.getenv("FAST_CHAT_MODEL", os.getenv("AI_FAST_MODEL", "gpt-4o-mini"))
    QUALITY_CHAT_MODEL: str = os.getenv("QUALITY_CHAT_MODEL", os.getenv("AI_MODEL", "gpt-4o-mini"))
    AI_REASONING_MODEL: str = os.getenv("AI_REASONING_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHAT_HISTORY_LIMIT: int = int(os.getenv("CHAT_HISTORY_LIMIT", "10"))
    MAX_CONTEXT_CHARS: int = int(os.getenv("MAX_CONTEXT_CHARS", "16000"))

    # Agent Limits — Phase 7
    AGENT_MAX_STEPS: int = int(os.getenv("AGENT_MAX_STEPS", "8"))
    AGENT_MAX_TOOL_CALLS: int = int(os.getenv("AGENT_MAX_TOOL_CALLS", "10"))
    AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))
    TOOL_MAX_RETRIES: int = int(os.getenv("TOOL_MAX_RETRIES", "2"))

    # Code Execution Sandbox — Phase 7
    CODE_EXECUTION_TIMEOUT: int = int(os.getenv("CODE_EXECUTION_TIMEOUT", "10"))
    CODE_EXECUTION_MEMORY_MB: int = int(os.getenv("CODE_EXECUTION_MEMORY_MB", "256"))
    CODE_EXECUTION_MAX_OUTPUT: int = int(os.getenv("CODE_EXECUTION_MAX_OUTPUT", "10000"))
    CODE_EXECUTION_MAX_CODE_SIZE: int = int(os.getenv("CODE_EXECUTION_MAX_CODE_SIZE", "50000"))

    # Database connection pooling properties
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

    # Redis Config
    REDIS_TIMEOUT: float = float(os.getenv("REDIS_TIMEOUT", "2.0"))
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "300"))


    # Rate Limiting — Phase 7 & 8.4 Configurable Limits
    MAX_AGENT_RUNS_PER_MINUTE: int = int(os.getenv("MAX_AGENT_RUNS_PER_MINUTE", "60"))
    MAX_CODE_EXECUTIONS_PER_MINUTE: int = int(os.getenv("MAX_CODE_EXECUTIONS_PER_MINUTE", "10"))
    MAX_SEARCHES_PER_MINUTE: int = int(os.getenv("MAX_SEARCHES_PER_MINUTE", "20"))
    
    RATE_LIMIT_AUTH: int = int(os.getenv("RATE_LIMIT_AUTH", "5"))
    RATE_LIMIT_CHAT: int = int(os.getenv("RATE_LIMIT_CHAT", "30"))
    RATE_LIMIT_UPLOAD: int = int(os.getenv("RATE_LIMIT_UPLOAD", "10"))
    RATE_LIMIT_AGENT: int = int(os.getenv("RATE_LIMIT_AGENT", "10"))
    RATE_LIMIT_GENERAL: int = int(os.getenv("RATE_LIMIT_GENERAL", "100"))

    # Provider & Reliability Settings (Phase 8.5)
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60.0"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    MAX_FIRST_TOKEN_LATENCY_SECONDS: float = float(os.getenv("MAX_FIRST_TOKEN_LATENCY_SECONDS", "10.0"))
    LLM_CIRCUIT_FAILURE_THRESHOLD: int = int(os.getenv("LLM_CIRCUIT_FAILURE_THRESHOLD", "5"))
    LLM_CIRCUIT_COOLDOWN_SECONDS: int = int(os.getenv("LLM_CIRCUIT_COOLDOWN_SECONDS", "30"))
    MAX_TOKENS_PER_REQUEST: int = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4096"))
    MAX_DAILY_AI_REQUESTS: int = int(os.getenv("MAX_DAILY_AI_REQUESTS", "500"))
    
    # RAG Settings (Phase 8.5)
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_MAX_CONTEXT_TOKENS: int = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "6000"))
    RAG_MIN_RELEVANCE_SCORE: float = float(os.getenv("RAG_MIN_RELEVANCE_SCORE", "0.3"))

    @property
    def ai_is_real(self) -> bool:
        """True only when a valid non-placeholder API key is configured AND mock is not forced."""
        if self.AI_USE_MOCK:
            return False

        api_key = self.CLOUD_LLM_API_KEY or self.AI_API_KEY
        if not api_key:
            return False

        key_lower = api_key.lower().strip()

        placeholder_substrings = ("mock", "dummy", "fake", "placeholder", "test")
        placeholder_keys = (
            "", "your_llm_api_key_here", "dummy-local-key", "local-mock-key",
            "dev-openai-token", "test-key", "fake-key", "mock-key", "placeholder", None
        )

        if key_lower in placeholder_keys or any(sub in key_lower for sub in placeholder_substrings):
            return False

        if self.LLM_PROVIDER == "ollama":
            return True

        if key_lower == "ollama":
            return True

        # If it's a local Ollama base URL, we permit keys containing "local" but not "mock"/"dummy"/"fake"/"placeholder"
        if self.AI_BASE_URL and ("127.0.0.1:11434" in self.AI_BASE_URL or "localhost:11434" in self.AI_BASE_URL):
            return True

        return True


    @property
    def RAG_RELEVANCE_THRESHOLD(self) -> float:
        return self.RAG_MIN_RELEVANCE_SCORE

    # Context management (Phase 8.5)
    MAX_CONTEXT_MESSAGES: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "30"))
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "12000"))

    # Agent controls (Phase 8.5)
    MAX_AGENT_STEPS: int = int(os.getenv("MAX_AGENT_STEPS", "10"))
    AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "120"))
    TOOL_TIMEOUT_SECONDS: int = int(os.getenv("TOOL_TIMEOUT_SECONDS", "30"))
    MAX_TOOL_OUTPUT_CHARS: int = int(os.getenv("MAX_TOOL_OUTPUT_CHARS", "20000"))

    @property
    def cors_origins(self) -> List[str]:
        # Split CORS origins by comma and clean whitespace
        origins = [url.strip() for url in self.FRONTEND_URL.split(",") if url.strip()]
        default_prod = "https://nova-ai-chat-pi.vercel.app"
        if default_prod not in origins:
            origins.append(default_prod)
        return origins

    @field_validator("AI_BASE_URL")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("AI_BASE_URL must be a valid HTTP/HTTPS URL")
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENV_MODE == "production":
            import logging
            logger = logging.getLogger("app.config")
            default_secret = "nova-premium-secret-token-key-change-in-prod-11223344"
            placeholder_secret = "your_jwt_signing_secret_here_must_be_at_least_32_chars"
            if self.JWT_SECRET in (default_secret, placeholder_secret) or len(self.JWT_SECRET) < 32:
                logger.warning("In production mode, JWT_SECRET should be set to a secure, unique, and long value (at least 32 characters)")
            if self.DATABASE_URL.startswith("sqlite"):
                logger.warning("In production mode, SQLite is in use.")
            if not self.REDIS_URL:
                logger.warning("In production mode, REDIS_URL is not configured. Falling back to in-memory cache.")
            if self.AI_USE_MOCK:
                logger.warning("In production mode, AI_USE_MOCK is true.")
            
            effective_key = self.CLOUD_LLM_API_KEY or self.AI_API_KEY
            if self.LLM_PROVIDER != "ollama" and (not effective_key or effective_key in ("your_llm_api_key_here", "local-mock-key", "dummy-local-key")):
                logger.warning("In production mode, cloud LLM key is placeholder or missing.")
            if "*" in self.cors_origins:
                logger.warning("CORS wildcard '*' should not be used in production mode.")
        return self


# Instantiate global settings
settings = Settings()
