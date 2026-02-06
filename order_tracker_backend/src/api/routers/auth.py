from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user
from src.auth.security import create_access_token, hash_password, verify_password
from src.db.models import NotificationPreference, NotificationChannel, User, UserRole
from src.db.session import get_db
from src.schemas import LoginRequest, SignupRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer account",
    description="Self-service signup endpoint. Creates a customer user and default notification preferences.",
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> UserPublic:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password), role=UserRole.customer)
    db.add(user)
    db.flush()

    # Default notification preferences
    pref = NotificationPreference(user_id=user.id, enabled=True, channel=NotificationChannel.email, email=user.email)
    db.add(pref)
    db.flush()

    return UserPublic(id=user.id, email=user.email, role=user.role, created_at=user.created_at)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description="Returns a bearer JWT token to authenticate subsequent requests.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
    description="Returns the authenticated user's public profile.",
)
def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, role=user.role, created_at=user.created_at)
