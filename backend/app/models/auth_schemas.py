"""
Authentication schemas for EvaluAI.
Pydantic models for login, password setup, and token responses.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr = Field(..., description="Employee email address")
    password: str = Field("", description="Employee password (empty on first login attempt)")


class SetPasswordRequest(BaseModel):
    """First-time password setup request."""
    email: EmailStr = Field(..., description="Employee email address")
    password: str = Field(..., min_length=6, description="New password (min 6 characters)")
    password_confirm: str = Field(..., description="Password confirmation")


# ═══════════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════════

class EmployeeInfo(BaseModel):
    """Public employee information returned after authentication."""
    employee_id: str
    email: EmailStr
    department: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    years_in_company: Optional[int] = None


class LoginResponse(BaseModel):
    """Successful login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    employee: EmployeeInfo


class MustSetPasswordResponse(BaseModel):
    """Response when employee has no password set yet."""
    must_set_password: bool = True
    email: EmailStr
    message: str = "First login: please create your password"
