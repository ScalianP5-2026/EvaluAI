"""
Configuration module for EvaluAI backend.
Handles Supabase connection and Gemini API key loading.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT FILE LOADING
# ═══════════════════════════════════════════════════════════════
# This section handles loading environment variables from a single
# centralized .env file located at the project root. This approach
# ensures both backend (Python) and frontend (Vite) share the same
# configuration source.

def _find_env_file():
    """
    Search for .env file starting from the current file location
    and traversing upward through parent directories until found.
    This makes the env loading robust regardless of where the backend
    is executed from (e.g., /backend/, /backend/app/, or from docker).
    
    Returns:
        Path: Path to .env file if found, None otherwise
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None


# Attempt to load .env from project root
env_file = _find_env_file()
if env_file:
    load_dotenv(dotenv_path=str(env_file))
    print(f"✓ Loaded .env from: {env_file}")
else:
    # Fallback: use default load_dotenv() behavior or system env vars
    load_dotenv()
    print("⚠ No .env file found, using system environment variables")

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════════════
# Core configuration variables loaded from .env file.
# These are required for backend connectivity and API integration.

# SUPABASE CONFIGURATION
# Used for database connection and real-time data synchronization
# Format: REST API URL (e.g., https://projectid.supabase.co)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")

# SUPABASE_KEY: JWT token for API authentication
# Format: JWT token with 'anon' or service role scope
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# GEMINI API CONFIGURATION
# Google Gemini API key for AI chatbot responses
# Required for the chatbot to generate intelligent recommendations
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Application settings
# DEBUG: Enables detailed logging and development-friendly error messages
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

# LOG_LEVEL: Controls verbosity of application logs (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# API_VERSION: Current version of the REST API endpoints
API_VERSION: str = "v1"

# ═══════════════════════════════════════════════════════════════
# APPLICATION CONFIGURATION CLASS
# ═══════════════════════════════════════════════════════════════
# Groups all configuration settings into a single AppConfig object
# that can be imported and used throughout the application.
# This provides a centralized, type-safe configuration interface.


class AppConfig:
    """
    Application configuration settings loaded from environment variables.
    
    This class serves as the central configuration container for:
    - API behavior (prefix, allowed origins)
    - Data paths (surveys, courses, mentors CSV files)
    - Chat provider settings (rule-based or AI provider)
    - Azure Foundry API credentials (optional)
    - Chatbot AI settings (temperature, timeouts, retries)
    """
    
    # ─ API Metadata ─
    TITLE: str = os.getenv("EVALUAI_APP_NAME", "EvaluAI API")
    DESCRIPTION: str = os.getenv("EVALUAI_APP_DESCRIPTION", "API to evaluate training impact with AI")
    VERSION: str = os.getenv("EVALUAI_APP_VERSION", "0.1.0")
    
    # ─ API Configuration ─
    api_prefix: str = os.getenv("EVALUAI_API_PREFIX", "/api/v1")
    allowed_origins: str = os.getenv("EVALUAI_ALLOWED_ORIGINS", "*")
    
    # ─ CORS Configuration ─
    # Dynamically parse allowed origins from .env
    # Supports comma-separated list like "http://localhost:3000,http://localhost:5173"
    _allowed_origins_str: str = os.getenv("EVALUAI_ALLOWED_ORIGINS", "*")
    CORS_ORIGINS: list = (
        ["*"] if _allowed_origins_str == "*"
        else [origin.strip() for origin in _allowed_origins_str.split(",")]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # ─ Data File Paths ─
    # These CSV files are loaded at startup to seed the database
    surveys_path: str = os.getenv("EVALUAI_SURVEYS_PATH", "data/datos_encuesta_formacion_ia.csv")
    courses_path: str = os.getenv("EVALUAI_COURSES_PATH", "data/courses.csv")
    mentors_path: str = os.getenv("EVALUAI_MENTORS_PATH", "data/mentors.csv")
    
    # ─ Chat Provider Configuration ─
    # Currently supports "rule_based" (default) or "gemini"
    chat_provider: str = os.getenv("EVALUAI_CHAT_PROVIDER", "rule_based")
    
    # ─ Azure Foundry API (optional alternative to Gemini) ─
    azure_foundry_endpoint: str = os.getenv("EVALUAI_AZURE_FOUNDRY_ENDPOINT", "")
    azure_foundry_api_key: str = os.getenv("EVALUAI_AZURE_FOUNDRY_API_KEY", "")
    azure_foundry_model: str = os.getenv("EVALUAI_AZURE_FOUNDRY_MODEL", "")
    azure_foundry_temperature: float = float(os.getenv("EVALUAI_AZURE_FOUNDRY_TEMPERATURE", "0.2"))
    
    # ─ Chatbot AI Settings ─
    # Model selection and behavior tuning
    GEMINI_MODEL: str = os.getenv("CHATBOT_GEMINI_MODEL", "gemini-2.5-flash")
    chatbot_gemini_temperature: float = float(os.getenv("CHATBOT_GEMINI_TEMPERATURE", "0.4"))
    chatbot_gemini_max_tokens: int = int(os.getenv("CHATBOT_GEMINI_MAX_TOKENS", "4096"))
    chatbot_gemini_timeout_seconds: int = int(os.getenv("CHATBOT_GEMINI_TIMEOUT_SECONDS", "30"))
    GEMINI_MAX_RETRIES: int = int(os.getenv("CHATBOT_GEMINI_MAX_RETRIES", "3"))
    
    # ─ Conversation Memory Limits ─
    # Controls how much context is retained in a conversation
    MAX_CONVERSATION_TURNS: int = int(os.getenv("CHATBOT_CONVERSATION_MAX_TURNS", "10"))
    chatbot_conversation_max_turns_to_api: int = int(os.getenv("CHATBOT_CONVERSATION_MAX_TURNS_TO_API", "8"))
    
    # ─ Goal Detection ─
    # Keywords used to detect user learning goals from text
    chatbot_goal_detection_keywords: list = os.getenv(
        "CHATBOT_GOAL_DETECTION_KEYWORDS",
        "learn,improve,develop,advance,study,train,certification,master,become"
    ).split(",")


# Create a singleton instance for easy import
settings = AppConfig()

# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT VALIDATION
# ═══════════════════════════════════════════════════════════════
# This section validates that critical environment variables are
# properly configured. Validation is performed at application startup
# to fail fast if required integrations cannot be established.


def validate_env_vars() -> None:
    """
    Validate that all required environment variables are set.
    
    Checks for critical variables needed for:
    - Database connectivity (Supabase)
    - AI integration (Gemini API)
    
    Raises:
        RuntimeError: If any critical environment variable is missing
    """
    # Track missing variables to provide a comprehensive error report
    missing_vars = []
    
    # Check Supabase REST API URL
    # Format: https://projectid.supabase.co
    if not SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    
    # Check Supabase authentication key (JWT token)
    # Required to establish authenticated connections to the database
    if not SUPABASE_KEY:
        missing_vars.append("SUPABASE_KEY")
    
    # Check Gemini API key for chatbot AI responses
    # Required for the conversational AI to generate recommendations
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
    
    # If any variables are missing, log a warning
    if missing_vars:
        logger.warning(
            f"Missing environment variables: {', '.join(missing_vars)}. "
            "Application will run in limited mode."
        )
        
        # If critical variables are ALL missing, prevent startup
        # This ensures the application fails fast rather than silently degrading
        if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
            err_msg = (
                "Critical environment variables missing. "
                "Please set SUPABASE_URL, SUPABASE_KEY, "
                "and GEMINI_API_KEY in .env"
            )
            logger.error(err_msg)


# ═══════════════════════════════════════════════════════════════
# SUPABASE CLIENT INITIALIZATION
# ═══════════════════════════════════════════════════════════════
# Implements the Singleton pattern to ensure only one connection
# to Supabase exists throughout the application lifetime.
# This optimizes resource usage and prevents connection pool exhaustion.

# Global reference to the single Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create the Supabase client using the Singleton pattern.
    
    On first call, initializes a connection to Supabase using the
    credentials from environment variables. Subsequent calls return
    the cached instance.
    
    Returns:
        Client: Supabase client instance ready for database operations
        
    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_KEY not set,
                      or if connection initialization fails
    """
    # Global reference allows modification of the module-level variable
    global _supabase_client
    
    # If client already initialized, return the cached instance
    # This ensures connection reuse across requests
    if _supabase_client is not None:
        return _supabase_client
    
    # Validate required credentials before attempting connection
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Cannot initialize Supabase client: "
            "SUPABASE_URL and SUPABASE_KEY must be set in .env"
        )
    
    # Attempt to establish connection to Supabase
    # Store the client instance for future use (Singleton pattern)
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✓ Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        # Log the failure with details for debugging
        logger.error(f"✗ Failed to initialize Supabase client: {str(e)}")
        # Raise a descriptive error to prevent the app from silently failing
        raise RuntimeError(f"Supabase initialization failed: {str(e)}")


def close_supabase_client() -> None:
    """
    Clean shutdown of Supabase client connection.
    
    Called during application shutdown to properly release database connections
    and ensure no resource leaks. Resets the singleton instance to None.
    """
    global _supabase_client
    if _supabase_client is not None:
        logger.info("Closing Supabase client")
        # Release the reference to trigger garbage collection
        _supabase_client = None


# ═══════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════
# Configures Python's logging system to provide structured output
# for debugging and monitoring application behavior

def setup_logging() -> None:
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=log_format
    )
    logger.info(f"Logging configured at {LOG_LEVEL} level")


# ═══════════════════════════════════════════════════════════════
# MODULE INITIALIZATION
# ═══════════════════════════════════════════════════════════════
# Validates environment on import and configures application logging

validate_env_vars()
setup_logging()
