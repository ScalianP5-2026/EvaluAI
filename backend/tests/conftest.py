"""
Shared pytest configuration for backend tests.

Adds the backend directory to sys.path so that `app.*` imports
work consistently when running pytest from the repo root.
"""

import sys
from pathlib import Path

# Add backend/ to sys.path so `from app.main import app` resolves correctly
sys.path.insert(0, str(Path(__file__).parent.parent))
