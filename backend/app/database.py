"""
NexaCart AI Support Bot - Database Layer

Provides SQLAlchemy engine, session factory, and utility functions.
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base


def _get_engine():
    """Create and return a SQLAlchemy engine, ensuring the parent directory exists."""
    db_url = settings.DATABASE_URL
    # For SQLite, ensure the directory exists
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
    return create_engine(
        db_url,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        echo=False,
    )


engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures it is closed
    after the request completes.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables defined in the ORM models if they do not exist."""
    Base.metadata.create_all(bind=engine)
