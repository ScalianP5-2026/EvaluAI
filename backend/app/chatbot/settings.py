"""
Settings for EvaluAI Chatbot Core.

Loads configuration from environment variables (.env file).
All parameters can be overridden by setting environment variables.
"""

import os
from typing import List


def _as_bool(value: str, default: bool = False) -> bool:
    """Parse common boolean env values."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# ==================== LLM PROVIDER ====================
# Supported values: "gemini" (default), "foundry", "azure_foundry", "azure_openai"

LLM_PROVIDER: str = os.getenv("CHATBOT_LLM_PROVIDER", "gemini").strip().lower()
"""Active LLM provider for chatbot responses"""

# ==================== GEMINI API CONFIG ====================
# Load from environment with defaults

GEMINI_API_KEY: str = os.getenv("CHATBOT_GEMINI_API_KEY", "")
"""Google Gemini API Key"""

GEMINI_MODEL: str = os.getenv("CHATBOT_GEMINI_MODEL", "gemini-2.5-flash")
"""Gemini model to use"""

GEMINI_TEMPERATURE: float = float(os.getenv("CHATBOT_GEMINI_TEMPERATURE", "0.4"))
"""Temperature for response consistency (0.0-1.0)"""

GEMINI_MAX_TOKENS: int = int(os.getenv("CHATBOT_GEMINI_MAX_TOKENS", "800"))
"""Max output tokens (concise responses)"""

GEMINI_TIMEOUT_SECONDS: int = int(os.getenv("CHATBOT_GEMINI_TIMEOUT_SECONDS", "30"))
"""Request timeout in seconds"""

GEMINI_MAX_RETRIES: int = int(os.getenv("CHATBOT_GEMINI_MAX_RETRIES", "3"))
"""Number of retry attempts on failure"""

# ==================== AZURE FOUNDRY / AZURE OPENAI ====================

FOUNDRY_API_KEY: str = os.getenv("CHATBOT_FOUNDRY_API_KEY", "")
"""Azure OpenAI / Foundry API key"""

FOUNDRY_ENDPOINT: str = os.getenv("CHATBOT_FOUNDRY_ENDPOINT", "")
"""Endpoint URL (resource base, deployment base, or full chat completions URL)"""

FOUNDRY_DEPLOYMENT: str = os.getenv("CHATBOT_FOUNDRY_DEPLOYMENT", "")
"""Deployment name (required if endpoint is only the resource base URL)"""

FOUNDRY_API_VERSION: str = os.getenv("CHATBOT_FOUNDRY_API_VERSION", "2025-01-01-preview")
"""Azure OpenAI API version"""

FOUNDRY_TEMPERATURE: float = float(os.getenv("CHATBOT_FOUNDRY_TEMPERATURE", "0.4"))
"""Temperature for Foundry responses"""

FOUNDRY_MAX_TOKENS: int = int(os.getenv("CHATBOT_FOUNDRY_MAX_TOKENS", "800"))
"""Max output tokens for Foundry responses"""

FOUNDRY_TIMEOUT_SECONDS: int = int(os.getenv("CHATBOT_FOUNDRY_TIMEOUT_SECONDS", "30"))
"""Request timeout in seconds"""

FOUNDRY_MAX_RETRIES: int = int(os.getenv("CHATBOT_FOUNDRY_MAX_RETRIES", "3"))
"""Number of retry attempts on failure"""

FOUNDRY_SYSTEM_PROMPT: str = os.getenv(
    "CHATBOT_FOUNDRY_SYSTEM_PROMPT",
    (
        "You are Scalian's internal learning advisor chatbot. "
        "Your responsibility is to provide practical, accurate, and personalized "
        "educational guidance to Scalian employees.\n"
        "Scope:\n"
        "- Recommend relevant courses, programs, and mentors based on provided context.\n"
        "- Answer employee profile questions only using supplied facts.\n"
        "- If information is unavailable in context, say so clearly and avoid guessing.\n"
        "Style:\n"
        "- Be concise, helpful, and professional.\n"
        "- Prefer clear, actionable next steps.\n"
        "Safety and policy:\n"
        "- Do not fabricate employee data, internal policies, or contacts.\n"
        "- Do not reveal secrets, credentials, or implementation internals.\n"
        "- Refuse requests outside learning advisory scope when needed.\n"
        "Output contract:\n"
        "- Follow the requested response schema exactly."
    ),
)
"""System prompt for Foundry chat completions."""

FOUNDRY_USE_STRUCTURED_OUTPUTS: bool = _as_bool(
    os.getenv("CHATBOT_FOUNDRY_USE_STRUCTURED_OUTPUTS", "true"),
    default=True,
)
"""Enable schema-enforced structured outputs on Foundry chat completions."""

FOUNDRY_STRUCTURED_SCHEMA_NAME: str = os.getenv(
    "CHATBOT_FOUNDRY_STRUCTURED_SCHEMA_NAME",
    "evaluai_chat_response",
)
"""Name used for Foundry structured output schema."""

FOUNDRY_STRUCTURED_SCHEMA_STRICT: bool = _as_bool(
    os.getenv("CHATBOT_FOUNDRY_STRUCTURED_SCHEMA_STRICT", "true"),
    default=True,
)
"""Whether structured output schema enforcement should be strict."""


# ==================== CONVERSATION MEMORY ====================

CONVERSATION_MAX_TURNS: int = int(os.getenv("CHATBOT_CONVERSATION_MAX_TURNS", "10"))
"""Maximum turns stored in memory"""

CONVERSATION_MAX_TURNS_TO_API: int = int(os.getenv("CHATBOT_CONVERSATION_MAX_TURNS_TO_API", "8"))
"""Maximum turns sent to Gemini API (token limit awareness)"""


# ==================== GOAL DETECTION ====================

# Parse keywords from comma-separated string
_keywords_str = os.getenv(
    "CHATBOT_GOAL_DETECTION_KEYWORDS",
    "learn,improve,develop,advance,study,train,certification,master,become"
)
GOAL_DETECTION_KEYWORDS: List[str] = [
    k.strip() for k in _keywords_str.split(",") if k.strip()
]
"""Keywords to detect learning/training intent"""


# ==================== LOGGING ====================

LOG_LEVEL: str = os.getenv("CHATBOT_LOG_LEVEL", "INFO")
"""Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

DEBUG_MODE: bool = os.getenv("CHATBOT_DEBUG_MODE", "false").lower() in ("true", "1", "yes")
"""Enable debug mode for extra logging"""

LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Standard logging format"""


# ==================== VALIDATION ====================

def validate_settings() -> bool:
    """
    Validate critical settings.
    
    Returns:
        True if settings are valid, False otherwise
    """
    errors = []
    
    # Check required settings by provider
    if LLM_PROVIDER in ("foundry", "azure_foundry", "azure_openai"):
        if not FOUNDRY_API_KEY:
            errors.append("CHATBOT_FOUNDRY_API_KEY is not set")
        if not FOUNDRY_ENDPOINT:
            errors.append("CHATBOT_FOUNDRY_ENDPOINT is not set")
        if not FOUNDRY_DEPLOYMENT and "/deployments/" not in FOUNDRY_ENDPOINT:
            errors.append(
                "CHATBOT_FOUNDRY_DEPLOYMENT is not set and endpoint doesn't include deployment path"
            )
    else:
        if not GEMINI_API_KEY:
            errors.append("CHATBOT_GEMINI_API_KEY is not set")
    
    if GEMINI_TEMPERATURE < 0.0 or GEMINI_TEMPERATURE > 1.0:
        errors.append(f"CHATBOT_GEMINI_TEMPERATURE must be 0.0-1.0, got {GEMINI_TEMPERATURE}")

    if FOUNDRY_TEMPERATURE < 0.0 or FOUNDRY_TEMPERATURE > 1.0:
        errors.append(
            f"CHATBOT_FOUNDRY_TEMPERATURE must be 0.0-1.0, got {FOUNDRY_TEMPERATURE}"
        )
    
    if GEMINI_MAX_TOKENS < 1:
        errors.append(f"CHATBOT_GEMINI_MAX_TOKENS must be > 0, got {GEMINI_MAX_TOKENS}")
    
    if GEMINI_MAX_RETRIES < 1:
        errors.append(f"CHATBOT_GEMINI_MAX_RETRIES must be > 0, got {GEMINI_MAX_RETRIES}")
    
    if CONVERSATION_MAX_TURNS < 1:
        errors.append(f"CHATBOT_CONVERSATION_MAX_TURNS must be > 0, got {CONVERSATION_MAX_TURNS}")
    
    if CONVERSATION_MAX_TURNS_TO_API > CONVERSATION_MAX_TURNS:
        errors.append(
            f"CHATBOT_CONVERSATION_MAX_TURNS_TO_API ({CONVERSATION_MAX_TURNS_TO_API}) "
            f"cannot exceed CHATBOT_CONVERSATION_MAX_TURNS ({CONVERSATION_MAX_TURNS})"
        )
    
    if not GOAL_DETECTION_KEYWORDS:
        errors.append("CHATBOT_GOAL_DETECTION_KEYWORDS is empty")
    
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return False
    
    return True


# ==================== DEBUG INFO ====================

def print_settings() -> None:
    """Print current settings (for debugging)."""
    if DEBUG_MODE:
        print("\n=== Chatbot Core Settings ===")
        print(f"LLM Provider: {LLM_PROVIDER}")
        print(f"Gemini Model: {GEMINI_MODEL}")
        print(f"Foundry Deployment: {FOUNDRY_DEPLOYMENT or '(from endpoint)'}")
        print(f"Temperature: {GEMINI_TEMPERATURE}")
        print(f"Max Tokens: {GEMINI_MAX_TOKENS}")
        print(f"Timeout: {GEMINI_TIMEOUT_SECONDS}s")
        print(f"Retries: {GEMINI_MAX_RETRIES}")
        print(f"Foundry Structured Outputs: {FOUNDRY_USE_STRUCTURED_OUTPUTS}")
        print(f"Foundry Structured Schema: {FOUNDRY_STRUCTURED_SCHEMA_NAME}")
        print(f"Memory Turns: {CONVERSATION_MAX_TURNS}")
        print(f"API Turns: {CONVERSATION_MAX_TURNS_TO_API}")
        print(f"Goal Keywords: {', '.join(GOAL_DETECTION_KEYWORDS)}")
        print(f"Log Level: {LOG_LEVEL}")
        print("============================\n")
