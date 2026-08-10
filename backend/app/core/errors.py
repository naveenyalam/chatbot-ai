"""
Normalized error hierarchy for NOVA AI.
All errors expose a safe user_message that can be sent to the frontend.
Internal details are logged but never surfaced to end users.
"""

class NOVABaseError(Exception):
    """Base class for all NOVA AI application errors."""
    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        self.user_message = user_message or "An unexpected error occurred. Please try again."

class AIServiceError(NOVABaseError):
    """Raised when the LLM provider returns an error or is unreachable."""
    def __init__(self, message: str):
        super().__init__(
            message,
            user_message="NOVA's AI service is temporarily unavailable. Please try again in a moment."
        )

class AIProviderNotConfiguredError(NOVABaseError):
    """Raised when no AI_API_KEY is configured."""
    def __init__(self, details: str = ""):
        super().__init__(
            f"AI_PROVIDER_NOT_CONFIGURED: {details}",
            user_message="⚠️ AI provider is not configured. Please configure an AI API key in backend/.env."
        )

class AIProviderAuthError(NOVABaseError):
    """Raised when authentication with the AI provider fails."""
    def __init__(self, details: str = ""):
        super().__init__(
            f"AI_PROVIDER_AUTH_ERROR: {details}",
            user_message="⚠️ AI Provider authentication failed. Please check your AI_API_KEY in backend/.env."
        )

class AIProviderUnavailableError(NOVABaseError):
    """Raised when the AI provider endpoint is unreachable."""
    def __init__(self, details: str = ""):
        super().__init__(
            f"AI_PROVIDER_UNAVAILABLE: {details}",
            user_message="⚠️ AI Provider is unreachable or service is down. Please try again later."
        )

class AIProviderRateLimitError(NOVABaseError):
    """Raised when AI provider rate limit is hit."""
    def __init__(self, details: str = ""):
        super().__init__(
            f"AI_PROVIDER_RATE_LIMIT: {details}",
            user_message="⚠️ AI Provider rate limit reached. Please wait a moment before sending another message."
        )

class ToolExecutionError(NOVABaseError):
    """Raised when a tool fails to execute."""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' failed: {reason}",
            user_message=f"The {tool_name} tool encountered an issue. NOVA will continue without it."
        )

class SandboxError(NOVABaseError):
    """Raised when the code execution sandbox encounters a problem."""
    def __init__(self, reason: str):
        super().__init__(
            f"Sandbox execution failed: {reason}",
            user_message="Code execution failed in the sandbox. Check your code and try again."
        )

class AgentTimeoutError(NOVABaseError):
    """Raised when an agent exceeds its configured time limit."""
    def __init__(self, timeout_seconds: int):
        super().__init__(
            f"Agent timed out after {timeout_seconds}s",
            user_message=f"NOVA stopped the task because it reached the {timeout_seconds}s execution time limit."
        )

class AgentStepLimitError(NOVABaseError):
    """Raised when an agent exceeds its maximum step count."""
    def __init__(self, max_steps: int):
        super().__init__(
            f"Agent exceeded max steps ({max_steps})",
            user_message=f"NOVA reached the maximum step limit ({max_steps}) for this task."
        )

class RateLimitError(NOVABaseError):
    """Raised when a user exceeds their rate limit for an operation."""
    def __init__(self, operation: str):
        super().__init__(
            f"Rate limit exceeded for operation: {operation}",
            user_message=f"You've made too many requests. Please wait a moment before trying again."
        )

class CalculatorError(NOVABaseError):
    """Raised when a calculator expression is invalid or unsafe."""
    def __init__(self, reason: str):
        super().__init__(
            f"Calculator error: {reason}",
            user_message=f"Invalid expression: {reason}"
        )

class UserIsolationError(NOVABaseError):
    """Raised when a user attempts to access another user's resources."""
    def __init__(self):
        super().__init__(
            "Cross-user resource access attempt blocked",
            user_message="You do not have permission to access this resource."
        )
