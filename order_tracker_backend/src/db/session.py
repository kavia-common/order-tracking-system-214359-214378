from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings


def _build_sqlalchemy_url() -> str:
    """
    Build SQLAlchemy database URL from environment variables.

    Resolution order:
    1) If POSTGRES_URL is set and looks like a full DSN (starts with postgresql:// or postgres://),
       use it as-is.
    2) If POSTGRES_URL is set but is just a hostname/service name (common in container setups),
       compose a DSN from POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT + host.
    3) Otherwise, compose from POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT and assume host=localhost.

    Raises:
        RuntimeError: if insufficient DB configuration exists.
    """
    settings = get_settings()

    if settings.postgres_url:
        # Full DSN path (preferred)
        if settings.postgres_url.startswith("postgresql://") or settings.postgres_url.startswith("postgres://"):
            return settings.postgres_url

    # Compose from pieces
    if not (settings.postgres_user and settings.postgres_password and settings.postgres_db and settings.postgres_port):
        raise RuntimeError(
            "Database configuration missing. Set POSTGRES_URL (DSN or host) or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT."
        )

    # If POSTGRES_URL is present but not a DSN, treat it as host (service name).
    host = settings.postgres_url or "localhost"
    return f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}@{host}:{settings.postgres_port}/{settings.postgres_db}"


_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


def init_engine() -> None:
    """Initialize SQLAlchemy engine and session factory (idempotent)."""
    global _ENGINE, _SessionLocal
    if _ENGINE is not None and _SessionLocal is not None:
        return

    db_url = _build_sqlalchemy_url()
    _ENGINE = create_engine(db_url, pool_pre_ping=True, future=True)
    _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)


def get_engine() -> Engine:
    """Get initialized engine."""
    if _ENGINE is None:
        init_engine()
    assert _ENGINE is not None
    return _ENGINE


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None

    db: Session = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a DB session."""
    with session_scope() as db:
        yield db
