"""
auth_handler.py — Password hashing and JWT token management for Orrbit.

Handles:
- Hashing passwords securely with bcrypt
- Verifying passwords on login
- Creating JWT tokens after successful login
- Verifying JWT tokens on every request
"""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ── Config ─────────────────────────────────────────────────────────────────────

# Change this to a long random string in production!
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "orrbit-super-secret-key-change-in-production")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ── Password hashing ───────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ─────────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Create a JWT token containing user data.
    Token expires after ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Returns the payload dict or raises an exception.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency ─────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency — extracts and returns the user_id from the JWT token.
    Use this in any route that requires authentication.

    Example:
        @app.post("/chat")
        def chat(user_id: str = Depends(get_current_user_id)):
            ...
    """
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not identify user from token.",
        )
    return user_id


def get_current_user_optional(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False))
) -> str | None:
    """
    Same as get_current_user_id but returns None instead of raising
    an error if no token is provided. Used for optional auth routes.
    """
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except HTTPException:
        return None