from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables (safe to call multiple times)
load_dotenv()

# Build DB URL from environment variables (may be incomplete until runtime)
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Declarative base is safe to create at import time
Base = declarative_base()

# Module-level placeholders that will be initialized via `init_engine()`
_engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def init_engine(url: str | None = None, **create_engine_kwargs) -> None:
    """
    Initialize the SQLAlchemy engine and sessionmaker. Call this during
    application startup (for example in FastAPI lifespan) so imports don't
    fail at module import time.

    If `url` is not provided, the module-level `SQLALCHEMY_DATABASE_URL` is used.
    """
    global _engine, SessionLocal

    if _engine is not None and SessionLocal is not None:
        return

    url = url or SQLALCHEMY_DATABASE_URL
    if not url or "None" in url:
        raise RuntimeError("Database URL is not configured. Set DB_* env vars.")

    # sensible defaults for a synchronous engine used in FastAPI startup
    defaults = dict(pool_pre_ping=True, pool_recycle=3600, future=True)
    defaults.update(create_engine_kwargs)

    _engine = create_engine(url, **defaults)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine, future=True)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    return _engine


def get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("SessionLocal not initialized. Call init_engine() first.")
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get DB session for FastAPI endpoints.

    Usage: `db: Session = Depends(get_db)`
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()