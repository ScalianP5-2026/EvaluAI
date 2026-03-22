"""
Access-control helpers for API routes.

Rules:
- RRHH users can access all features.
- Non-RRHH users are limited to chatbot features.
"""

from __future__ import annotations

from app.api.auth_routes import get_current_user
from app.models.auth_schemas import EmployeeInfo
from fastapi import Depends, HTTPException, status


def normalize_department(value: str | None) -> str:
    """Normalize department text for robust comparisons."""
    if not value:
        return ""
    normalized = value.strip().lower()
    normalized = normalized.replace(".", "").replace("_", " ")
    normalized = " ".join(normalized.split())
    return normalized


def is_rrhh_department(value: str | None) -> bool:
    """True when department corresponds to RRHH / Human Resources."""
    normalized = normalize_department(value)
    return normalized in {
        "rrhh",
        "rr hh",
        "recursos humanos",
        "human resources",
        "hr",
    }


def require_rrhh_access(
    current_user: EmployeeInfo = Depends(get_current_user),
) -> EmployeeInfo:
    """
    Allow access only to RRHH users.
    """
    if not is_rrhh_department(current_user.department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to RRHH users",
        )
    return current_user
