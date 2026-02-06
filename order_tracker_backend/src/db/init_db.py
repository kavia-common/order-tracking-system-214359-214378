from sqlalchemy import text

from src.db.models import Base
from src.db.session import get_engine


def init_db() -> None:
    """
    Initialize database schema.

    For this template project we use SQLAlchemy's metadata create_all to provision tables.
    In production you would typically use migrations (Alembic).
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Lightweight sanity check connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
