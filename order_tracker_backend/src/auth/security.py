from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from src.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return pwd_context.verify(password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(*, subject: str, role: str, expires_minutes: Optional[int] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: User id as string.
        role: 'customer' or 'admin'.
        expires_minutes: Optional override for token expiration time.

    Returns:
        Encoded JWT token string.

    Raises:
        RuntimeError: If JWT_SECRET is not configured.
    """
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not set; cannot issue tokens.")

    exp_minutes = expires_minutes or settings.access_token_exp_minutes
    now = datetime.now(UTC)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


# PUBLIC_INTERFACE
def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Returns:
        The decoded JWT payload.

    Raises:
        RuntimeError: If JWT_SECRET is not configured.
        jwt.InvalidTokenError: If the token is invalid/expired/claims mismatch.
    """
    settings = get_settings()
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not set; cannot validate tokens.")
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "sub", "role", "aud", "iss"]},
    )
