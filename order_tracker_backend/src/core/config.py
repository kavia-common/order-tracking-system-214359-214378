import os
from dataclasses import dataclass
from typing import List


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str
    app_version: str
    allowed_origins: List[str]
    allowed_methods: List[str]
    allowed_headers: List[str]
    cors_max_age: int

    postgres_url: str | None
    postgres_user: str | None
    postgres_password: str | None
    postgres_db: str | None
    postgres_port: str | None

    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    access_token_exp_minutes: int


def get_settings() -> Settings:
    """
    Load application settings.

    Notes:
    - Database settings are expected to be provided by the database container as env vars:
      POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
    - JWT_SECRET MUST be set for auth to work securely.
    """
    return Settings(
        app_name=os.getenv("APP_NAME", "Order Tracker Backend"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        allowed_origins=_split_csv(os.getenv("ALLOWED_ORIGINS", "*")),
        allowed_methods=_split_csv(os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,PATCH,OPTIONS")),
        allowed_headers=_split_csv(os.getenv("ALLOWED_HEADERS", "Content-Type,Authorization")),
        cors_max_age=int(os.getenv("CORS_MAX_AGE", "3600")),
        postgres_url=os.getenv("POSTGRES_URL"),
        postgres_user=os.getenv("POSTGRES_USER"),
        postgres_password=os.getenv("POSTGRES_PASSWORD"),
        postgres_db=os.getenv("POSTGRES_DB"),
        postgres_port=os.getenv("POSTGRES_PORT"),
        jwt_secret=os.getenv("JWT_SECRET", ""),
        jwt_issuer=os.getenv("JWT_ISSUER", "order-tracker"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "order-tracker-clients"),
        access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60")),
    )
