"""Reusable Supabase client for data loading scripts."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


def _find_env_file() -> Path | None:
    """Find the nearest .env file by traversing parents from this script."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None


def _load_environment() -> None:
    """Load environment variables from .env if available."""
    env_file = _find_env_file()
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()


_load_environment()


def get_supabase_client() -> Client:
    """Create and return an authenticated Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_KEY environment variable. "
            "Please configure them in the project .env file."
        )

    return create_client(supabase_url, supabase_key)
