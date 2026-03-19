"""
Integration tests for auth endpoints.

Covers:
- POST /api/v1/auth/login  (valid credentials, must_set_password, invalid)
- POST /api/v1/auth/set-password  (success, already set, mismatch)
- GET  /api/v1/auth/me  (valid token, invalid token)
"""

import os
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure JWT_SECRET_KEY is set before importing auth_routes (avoids RuntimeError in prod mode)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")

from app.api import auth_routes
from app.main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_supabase_mock(credentials=None, employees=None):
    """Build a Supabase MagicMock that returns given data rows."""
    mock_supabase = MagicMock()

    cred_result = MagicMock()
    cred_result.data = credentials if credentials is not None else []

    emp_result = MagicMock()
    emp_result.data = employees if employees is not None else []

    def table_side_effect(name):
        tbl = MagicMock()
        tbl.select.return_value.eq.return_value.execute.return_value = (
            cred_result if name == "user_credentials" else emp_result
        )
        tbl.update.return_value.eq.return_value.execute.return_value = MagicMock()
        return tbl

    mock_supabase.table.side_effect = table_side_effect
    return mock_supabase


def _valid_credential(with_password: bool = True) -> dict:
    hashed = auth_routes.hash_password("secret123") if with_password else None
    return {
        "employee_id": "emp-001",
        "email": "alice@example.com",
        "password_hash": hashed,
    }


def _valid_employee() -> dict:
    return {
        "employee_id": "emp-001",
        "department": "Engineering",
        "age": 30,
        "gender": "female",
        "education_level": "bachelor",
        "years_in_company": 3,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/login
# ─────────────────────────────────────────────────────────────────────────────

class TestLoginEndpoint:
    def test_login_success(self):
        """Valid credentials return a JWT token and employee info."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=True)],
            employees=[_valid_employee()],
        )
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "alice@example.com", "password": "secret123"},
            )
        assert response.status_code == 200
        payload = response.json()
        assert "access_token" in payload
        assert payload["token_type"] == "bearer"
        assert payload["employee"]["employee_id"] == "emp-001"

    def test_login_must_set_password(self):
        """Credential with no password hash triggers must_set_password response."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=False)],
        )
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "alice@example.com", "password": ""},
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["must_set_password"] is True
        assert payload["email"] == "alice@example.com"

    def test_login_invalid_password(self):
        """Wrong password returns 401."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=True)],
        )
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "alice@example.com", "password": "wrongpassword"},
            )
        assert response.status_code == 401

    def test_login_unknown_email(self):
        """Unknown email returns 401."""
        mock_supabase = _make_supabase_mock(credentials=[])
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "unknown@example.com", "password": "any"},
            )
        assert response.status_code == 401

    def test_login_invalid_email_format(self):
        """Malformed email is rejected by schema validation (422)."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "secret123"},
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/set-password
# ─────────────────────────────────────────────────────────────────────────────

class TestSetPasswordEndpoint:
    def test_set_password_success(self):
        """First-time password setup returns a JWT token."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=False)],
            employees=[_valid_employee()],
        )
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/set-password",
                json={
                    "email": "alice@example.com",
                    "password": "newpass1",
                    "password_confirm": "newpass1",
                },
            )
        assert response.status_code == 200
        payload = response.json()
        assert "access_token" in payload

    def test_set_password_mismatch(self):
        """Mismatched passwords return 400."""
        response = client.post(
            "/api/v1/auth/set-password",
            json={
                "email": "alice@example.com",
                "password": "newpass1",
                "password_confirm": "different",
            },
        )
        assert response.status_code == 400

    def test_set_password_already_set(self):
        """Trying to set password when one already exists returns 400."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=True)],
        )
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/set-password",
                json={
                    "email": "alice@example.com",
                    "password": "newpass1",
                    "password_confirm": "newpass1",
                },
            )
        assert response.status_code == 400

    def test_set_password_unknown_email(self):
        """Unknown email returns 404."""
        mock_supabase = _make_supabase_mock(credentials=[])
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.post(
                "/api/v1/auth/set-password",
                json={
                    "email": "ghost@example.com",
                    "password": "newpass1",
                    "password_confirm": "newpass1",
                },
            )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/auth/me
# ─────────────────────────────────────────────────────────────────────────────

class TestMeEndpoint:
    def _make_token(self) -> str:
        return auth_routes.create_access_token(
            {"sub": "emp-001", "email": "alice@example.com"},
            expires_delta=timedelta(minutes=30),
        )

    def test_me_valid_token(self):
        """Valid JWT returns current employee info."""
        mock_supabase = _make_supabase_mock(
            credentials=[_valid_credential(with_password=True)],
            employees=[_valid_employee()],
        )
        token = self._make_token()
        with patch("app.api.auth_routes.get_supabase_client", return_value=mock_supabase):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["employee_id"] == "emp-001"
        assert payload["email"] == "alice@example.com"

    def test_me_missing_token(self):
        """Missing Authorization header returns 401 or 403."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    def test_me_invalid_token(self):
        """Garbage JWT returns 401 or 403."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert response.status_code in (401, 403)
