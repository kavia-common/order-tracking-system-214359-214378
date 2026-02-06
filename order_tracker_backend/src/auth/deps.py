from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.security import decode_token
from src.db.models import User, UserRole
from src.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def _forbidden(detail: str = "Not authorized") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from Bearer token."""
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise _unauthorized("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token subject")

    user = db.scalar(select(User).where(User.id == int(user_id)))
    if user is None or not user.is_active:
        raise _unauthorized("User not found or inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if user.role != UserRole.admin:
        raise _forbidden("Admin role required")
    return user
