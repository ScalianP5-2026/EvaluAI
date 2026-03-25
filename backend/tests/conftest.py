"""
Shared pytest configuration for backend tests.

Adds the backend directory to sys.path so that `app.*` imports
work consistently when running pytest from the repo root.
"""

import sys
from pathlib import Path

import pytest

from app.api.access_control import require_rrhh_access
from app.models.auth_schemas import EmployeeInfo
from app.main import app

# Add backend/ to sys.path so `from app.main import app` resolves correctly
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def _override_rrhh_access():
	"""Allow protected ML/NLP/upload endpoints during tests unless overridden."""
	app.dependency_overrides[require_rrhh_access] = lambda: EmployeeInfo(
		employee_id="test-rrhh-001",
		email="rrhh@example.com",
		department="RRHH",
		age=30,
		gender=None,
		education_level="Bachelor",
		years_in_company=3,
	)
	yield
	app.dependency_overrides.pop(require_rrhh_access, None)
