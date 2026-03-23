"""
Settings for EvaluAI Chatbot Core.

Loads configuration from environment variables (.env file).
All parameters can be overridden by setting environment variables.
"""

import os
from typing import List

# ==================== GEMINI API CONFIG ====================
# Load from environment with defaults

GEMINI_API_KEY: str = os.getenv("CHATBOT_GEMINI_API_KEY", "")
"""Google Gemini API Key"""

GEMINI_MODEL: str = os.getenv("CHATBOT_GEMINI_MODEL", "gemini-2.5-flash")
"""Gemini model to use"""

GEMINI_TEMPERATURE: float = float(os.getenv("CHATBOT_GEMINI_TEMPERATURE", "0.4"))
"""Temperature for response consistency (0.0-1.0)"""

GEMINI_MAX_TOKENS: int = int(os.getenv("CHATBOT_GEMINI_MAX_TOKENS", "4096"))
"""Max output tokens (concise responses)"""

GEMINI_TIMEOUT_SECONDS: int = int(os.getenv("CHATBOT_GEMINI_TIMEOUT_SECONDS", "30"))
"""Request timeout in seconds"""

GEMINI_MAX_RETRIES: int = int(os.getenv("CHATBOT_GEMINI_MAX_RETRIES", "3"))
"""Number of retry attempts on failure"""


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
    
    # Check required settings
    if not GEMINI_API_KEY:
        errors.append("CHATBOT_GEMINI_API_KEY is not set")
    
    if GEMINI_TEMPERATURE < 0.0 or GEMINI_TEMPERATURE > 1.0:
        errors.append(f"CHATBOT_GEMINI_TEMPERATURE must be 0.0-1.0, got {GEMINI_TEMPERATURE}")
    
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
        print(f"Gemini Model: {GEMINI_MODEL}")
        print(f"Temperature: {GEMINI_TEMPERATURE}")
        print(f"Max Tokens: {GEMINI_MAX_TOKENS}")
        print(f"Timeout: {GEMINI_TIMEOUT_SECONDS}s")
        print(f"Retries: {GEMINI_MAX_RETRIES}")
        print(f"Memory Turns: {CONVERSATION_MAX_TURNS}")
        print(f"API Turns: {CONVERSATION_MAX_TURNS_TO_API}")
        print(f"Goal Keywords: {', '.join(GOAL_DETECTION_KEYWORDS)}")
        print(f"Log Level: {LOG_LEVEL}")
        print("============================\n")
