from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from src.db.models import NotificationChannel, OrderStatus, UserRole


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: Literal["bearer"] = Field("bearer", description="Token type")


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime


class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: Optional[UserRole] = Field(None, description="Optional role. Only honored if requester is admin (not in self-signup).")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OrderCreateRequest(BaseModel):
    order_number: str = Field(..., min_length=3, max_length=64, description="External/customer-visible order number")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class OrderUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class OrderStatusUpdateRequest(BaseModel):
    new_status: OrderStatus = Field(..., description="New order status")
    note: Optional[str] = Field(None, max_length=5000, description="Optional note for the status change")


class OrderStatusHistoryItem(BaseModel):
    id: int
    old_status: Optional[OrderStatus]
    new_status: OrderStatus
    changed_by_user_id: Optional[int]
    note: Optional[str]
    changed_at: datetime


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    title: str
    description: Optional[str]
    current_status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderResponse):
    history: list[OrderStatusHistoryItem] = Field(default_factory=list)


class NotificationPreferenceUpsertRequest(BaseModel):
    enabled: bool = Field(True, description="Enable/disable notifications")
    channel: NotificationChannel = Field(..., description="Preferred notification channel")
    email: Optional[EmailStr] = Field(None, description="Email address for email notifications")
    phone: Optional[str] = Field(None, description="Phone number for SMS notifications")
    push_token: Optional[str] = Field(None, description="Push token for push notifications")


class NotificationPreferenceResponse(BaseModel):
    enabled: bool
    channel: NotificationChannel
    email: Optional[EmailStr]
    phone: Optional[str]
    push_token: Optional[str]
    updated_at: datetime
