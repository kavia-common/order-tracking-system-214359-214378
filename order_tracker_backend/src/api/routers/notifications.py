from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.deps import get_current_user
from src.db.models import NotificationPreference, User
from src.db.session import get_db
from src.schemas import NotificationPreferenceResponse, NotificationPreferenceUpsertRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get notification preferences",
    description="Returns the authenticated user's current notification preferences.",
)
def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationPreferenceResponse:
    pref = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user.id))
    if pref is None:
        raise HTTPException(status_code=404, detail="Notification preferences not found")

    return NotificationPreferenceResponse(
        enabled=pref.enabled,
        channel=pref.channel,
        email=pref.email,
        phone=pref.phone,
        push_token=pref.push_token,
        updated_at=pref.updated_at,
    )


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update notification preferences",
    description="Upserts the authenticated user's notification preferences.",
)
def upsert_preferences(
    payload: NotificationPreferenceUpsertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationPreferenceResponse:
    pref = db.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user.id))
    if pref is None:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
        db.flush()

    pref.enabled = payload.enabled
    pref.channel = payload.channel
    pref.email = str(payload.email) if payload.email is not None else pref.email
    pref.phone = payload.phone
    pref.push_token = payload.push_token

    db.add(pref)
    db.flush()

    return NotificationPreferenceResponse(
        enabled=pref.enabled,
        channel=pref.channel,
        email=pref.email,
        phone=pref.phone,
        push_token=pref.push_token,
        updated_at=pref.updated_at,
    )
