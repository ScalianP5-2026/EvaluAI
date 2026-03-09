"""
Configuration module for EvaluAI backend.
Handles Supabase connection and Gemini API key loading.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════════════

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Application settings
DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
API_VERSION: str = "v1"

# ═══════════════════════════════════════════════════════════════
# Validation on startup
# ═══════════════════════════════════════════════════════════════


def validate_env_vars() -> None:
    """
    Validate that all required environment variables are set.
    Raises RuntimeError if critical vars are missing.
    """
    missing_vars = []
    
    if not SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing_vars.append("SUPABASE_KEY")
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
    
    if missing_vars:
        logger.warning(
            f"Missing environment variables: {', '.join(missing_vars)}. "
            "Application will run in limited mode."
        )
        if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
            err_msg = (
                "Critical environment variables missing. "
                "Please set SUPABASE_URL, SUPABASE_KEY, "
                "and GEMINI_API_KEY in .env"
            )
            logger.error(err_msg)


# ═══════════════════════════════════════════════════════════════
# Supabase Client (Singleton pattern)
# ═══════════════════════════════════════════════════════════════

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client (singleton).
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_KEY not set
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Cannot initialize Supabase client: "
            "SUPABASE_URL and SUPABASE_KEY must be set in .env"
        )
    
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✓ Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"✗ Failed to initialize Supabase client: {str(e)}")
        raise RuntimeError(f"Supabase initialization failed: {str(e)}")


def close_supabase_client() -> None:
    """Close Supabase client connection."""
    global _supabase_client
    if _supabase_client is not None:
        logger.info("Closing Supabase client")
        _supabase_client = None


# ═══════════════════════════════════════════════════════════════
# Logging Configuration
# ═══════════════════════════════════════════════════════════════

def setup_logging() -> None:
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=log_format
    )
    logger.info(f"Logging configured at {LOG_LEVEL} level")


# ═══════════════════════════════════════════════════════════════
# Application Configuration
# ═══════════════════════════════════════════════════════════════

class AppConfig:
    """Application configuration class."""
    
    # API Settings
    TITLE = "EvaluAI API"
    DESCRIPTION = "AI-powered training evaluation system for enterprises"
    VERSION = "1.0.0"
    API_PREFIX = f"/api/{API_VERSION}"
    
    # CORS Settings
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # Chat Settings
    MAX_MESSAGE_LENGTH = 2000
    MAX_CONVERSATION_TURNS = 10
    
    # Gemini Settings
    GEMINI_MODEL = "gemini-2.5-flash"
    GEMINI_MAX_RETRIES = 3
    GEMINI_TIMEOUT = 30


# Initialize on import
validate_env_vars()
setup_logging()
