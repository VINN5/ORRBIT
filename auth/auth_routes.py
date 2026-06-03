"""
auth_routes.py — Authentication endpoints for Orrbit.

Endpoints:
- POST /auth/register  → create a new account
- POST /auth/login     → login and get JWT token
- GET  /auth/me        → get current user info
- POST /auth/logout    → logout (client deletes token)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime

from auth.models import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    email_exists,
    username_exists,
)
from auth.auth_handler import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response schemas ─────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    username: str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    username:     str
    email:        str
    message:      str


class UserResponse(BaseModel):
    user_id:    str
    username:   str
    email:      str
    created_at: str
    last_login: str | None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest):
    """
    Register a new Orrbit user.
    Creates account and returns a JWT token immediately.
    """
    # Validate inputs
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters.",
        )

    if len(request.username) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 2 characters.",
        )

    # Check for duplicates
    if email_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    if username_exists(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken.",
        )

    # Create user
    hashed = hash_password(request.password)
    user   = create_user(
        email=request.email,
        username=request.username,
        hashed_password=hashed,
    )

    # Generate token
    token = create_access_token({"sub": user["_id"]})

    return AuthResponse(
        access_token=token,
        user_id=user["_id"],
        username=user["username"],
        email=user["email"],
        message=f"Welcome to Orrbit, {user['username']}! 🚀",
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """
    Login with email and password.
    Returns a JWT token on success.
    """
    # Find user
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email.",
        )

    # Check account is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again.",
        )

    # Update last login
    update_last_login(user["_id"])

    # Generate token
    token = create_access_token({"sub": user["_id"]})

    return AuthResponse(
        access_token=token,
        user_id=user["_id"],
        username=user["username"],
        email=user["email"],
        message=f"Welcome back, {user['username']}! 👋",
    )


@router.get("/me", response_model=UserResponse)
def get_me(user_id: str = Depends(get_current_user_id)):
    """
    Get the current logged-in user's profile.
    Requires a valid JWT token.
    """
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserResponse(
        user_id=user["_id"],
        username=user["username"],
        email=user["email"],
        created_at=user.get("created_at", ""),
        last_login=user.get("last_login"),
    )


@router.post("/logout")
def logout():
    """
    Logout endpoint.
    JWT tokens are stateless — the client simply deletes the token.
    """
    return {"message": "Logged out successfully. See you soon! 👋"}