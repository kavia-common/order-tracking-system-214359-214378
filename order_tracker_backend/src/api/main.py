from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import auth_router, notifications_router, orders_router
from src.core.config import get_settings
from src.db.init_db import init_db

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service health and basic diagnostics."},
    {"name": "Auth", "description": "Authentication endpoints (signup/login/me)."},
    {"name": "Orders", "description": "Order CRUD, lookup, and status history APIs."},
    {"name": "Notifications", "description": "Notification preference APIs."},
]

app = FastAPI(
    title=settings.app_name,
    description="Order Tracker backend API providing JWT auth, order tracking, status history, and notification preferences.",
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=settings.allowed_methods if settings.allowed_methods else ["*"],
    allow_headers=settings.allowed_headers if settings.allowed_headers else ["*"],
    max_age=settings.cors_max_age,
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize DB schema on application startup."""
    init_db()


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Basic health check endpoint.",
)
def health_check():
    return {"message": "Healthy"}


app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(notifications_router)
