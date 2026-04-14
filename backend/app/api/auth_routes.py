"""
Authentication Routes for EvaluAI.
Handles employee login, first-time password setup, and token validation.

Endpoints:
    POST /api/v1/auth/login        - Login with email + password
    POST /api/v1/auth/set-password  - First-time password creation
    GET  /api/v1/auth/me            - Get current user info from JWT
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_supabase_client
from app.models.auth_schemas import (
    EmployeeInfo,
    LoginRequest,
    LoginResponse,
    MustSetPasswordResponse,
    SetPasswordRequest,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Security Configuration
# ═══════════════════════════════════════════════════════════════

_JWT_SECRET_DEFAULT = "evaluai-dev-secret-key-change-in-production-2026"
_raw_jwt_secret = os.getenv("JWT_SECRET_KEY")

if not _raw_jwt_secret:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable must be set in production. "
            "Please configure it before starting the application."
        )
    logger.warning(
        "JWT_SECRET_KEY is not set. Using insecure default — DO NOT use in production."
    )
    _raw_jwt_secret = _JWT_SECRET_DEFAULT

JWT_SECRET_KEY = _raw_jwt_secret
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

BUILTIN_ADMIN_USERNAME = "admin"
BUILTIN_ADMIN_PASSWORD = "scalian"
BUILTIN_ADMIN_EMPLOYEE_ID = "admin"
BUILTIN_ADMIN_EMAIL = "admin@scalian.com"
BUILTIN_ADMIN_DEPARTMENT = "RRHH"


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _build_employee_info(credential: dict, employee: Optional[dict] = None) -> EmployeeInfo:
    """Build EmployeeInfo from credential and optional employee data."""
    return EmployeeInfo(
        employee_id=credential["employee_id"],
        email=credential["email"],
        department=employee.get("department") if employee else None,
        age=employee.get("age") if employee else None,
        gender=employee.get("gender") if employee else None,
        education_level=employee.get("education_level") if employee else None,
        years_in_company=employee.get("years_in_company") if employee else None,
    )


def _build_builtin_admin_info() -> EmployeeInfo:
    """Return the built-in admin profile (not stored in DB)."""
    return EmployeeInfo(
        employee_id=BUILTIN_ADMIN_EMPLOYEE_ID,
        email=BUILTIN_ADMIN_EMAIL,
        department=BUILTIN_ADMIN_DEPARTMENT,
        age=None,
        gender=None,
        education_level=None,
        years_in_company=None,
    )


# ═══════════════════════════════════════════════════════════════
# POST /api/v1/auth/login
# ═══════════════════════════════════════════════════════════════

@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate employee by email + password.
    
    If password_hash is NULL (first login), returns must_set_password response.
    If credentials are valid, returns JWT access token.
    """
    normalized_login = (request.email or "").strip().lower()

    # Built-in admin account (never persisted in database)
    if normalized_login == BUILTIN_ADMIN_USERNAME:
        if request.password != BUILTIN_ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        access_token = create_access_token(data={
            "sub": BUILTIN_ADMIN_EMPLOYEE_ID,
            "email": BUILTIN_ADMIN_EMAIL,
            "is_builtin_admin": True,
        })

        return LoginResponse(
            access_token=access_token,
            employee=_build_builtin_admin_info(),
        )

    supabase = get_supabase_client()
    
    # Look up employee credentials by email
    try:
        result = supabase.table("user_credentials").select("*").eq("email", request.email).execute()
    except Exception as e:
        logger.error(f"Database error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    credential = result.data[0]

    # Reject disabled accounts
    if not credential.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if password has been set
    if credential.get("password_hash") is None:
        return MustSetPasswordResponse(
            email=request.email,
            message="First login: please create your password"
        )
    
    # Verify password
    if not request.password or not verify_password(request.password, credential["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last_login timestamp
    try:
        supabase.table("user_credentials").update(
            {"last_login": datetime.now(timezone.utc).isoformat()}
        ).eq("email", request.email).execute()
    except Exception as e:
        logger.warning(f"Failed to update last_login: {e}")
    
    # Fetch employee details from employees table
    employee = None
    try:
        emp_result = supabase.table("employees").select("*").eq(
            "employee_id", credential["employee_id"]
        ).execute()
        if emp_result.data:
            employee = emp_result.data[0]
    except Exception as e:
        logger.warning(f"Could not fetch employee details: {e}")
    
    # Build response
    employee_info = _build_employee_info(credential, employee)
    access_token = create_access_token(data={
        "sub": credential["employee_id"],
        "email": credential["email"]
    })
    
    return LoginResponse(
        access_token=access_token,
        employee=employee_info
    )


# ═══════════════════════════════════════════════════════════════
# POST /api/v1/auth/set-password
# ═══════════════════════════════════════════════════════════════

@router.post("/set-password")
async def set_password(request: SetPasswordRequest):
    """
    First-time password setup for an employee.
    
    Only works if the employee's password_hash is currently NULL.
    After setting the password, returns a JWT token (auto-login).
    """
    # Validate password confirmation
    if request.password != request.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    if request.email.strip().lower() == BUILTIN_ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Built-in admin password cannot be changed",
        )
    
    supabase = get_supabase_client()
    
    # Look up employee credentials
    try:
        result = supabase.table("user_credentials").select("*").eq("email", request.email).execute()
    except Exception as e:
        logger.error(f"Database error during set-password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    credential = result.data[0]

    # Reject disabled accounts
    if not credential.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Ensure password hasn't been set already
    if credential.get("password_hash") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already set. Use login instead."
        )
    
    # Hash and store the password
    password_hash = hash_password(request.password)
    try:
        supabase.table("user_credentials").update({
            "password_hash": password_hash,
            "last_login": datetime.now(timezone.utc).isoformat()
        }).eq("email", request.email).execute()
    except Exception as e:
        logger.error(f"Failed to set password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save password"
        )
    
    # Fetch employee details
    employee = None
    try:
        emp_result = supabase.table("employees").select("*").eq(
            "employee_id", credential["employee_id"]
        ).execute()
        if emp_result.data:
            employee = emp_result.data[0]
    except Exception as e:
        logger.warning(f"Could not fetch employee details: {e}")
    
    # Build response with JWT (auto-login after setting password)
    employee_info = _build_employee_info(credential, employee)
    access_token = create_access_token(data={
        "sub": credential["employee_id"],
        "email": credential["email"]
    })
    
    logger.info(f"✓ Password set for employee {credential['employee_id']} ({request.email})")
    
    return LoginResponse(
        access_token=access_token,
        employee=employee_info
    )


# ═══════════════════════════════════════════════════════════════
# GET /api/v1/auth/me
# ═══════════════════════════════════════════════════════════════

@router.get("/me", response_model=EmployeeInfo)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current authenticated user info from JWT token.
    """
    payload = decode_access_token(credentials.credentials)
    
    employee_id = payload.get("sub")
    email = payload.get("email")
    
    if not employee_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    if payload.get("is_builtin_admin") is True:
        if employee_id != BUILTIN_ADMIN_EMPLOYEE_ID or email != BUILTIN_ADMIN_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        return _build_builtin_admin_info()
    
    supabase = get_supabase_client()
    
    # Fetch credential record
    try:
        cred_result = supabase.table("user_credentials").select("*").eq("email", email).execute()
    except Exception as e:
        logger.error(f"Database error in /me: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )
    
    if not cred_result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    credential = cred_result.data[0]

    # Reject disabled accounts
    if not credential.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Verify the credential belongs to the token subject to prevent mismatch
    if credential.get("employee_id") != employee_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject does not match credential"
        )

    # Fetch employee details
    employee = None
    try:
        emp_result = supabase.table("employees").select("*").eq(
            "employee_id", employee_id
        ).execute()
        if emp_result.data:
            employee = emp_result.data[0]
    except Exception as e:
        logger.warning(f"Could not fetch employee details: {e}")
    
    return _build_employee_info(credential, employee)
