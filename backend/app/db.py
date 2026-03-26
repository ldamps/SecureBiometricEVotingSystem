"""Database engine, session, and dependency for FastAPI.

Use get_db() in route dependencies to get a session. Call create_tables()
once to create all tables (e.g. from a script or on first run); for ongoing
changes use Alembic migrations instead.

Sync engine/SessionLocal are used by root routes (e.g. list_constituencies).
Async engine/session_factory are used by versioned API (e.g. voter routes)
and must be set on app.state at startup via init_async_db().
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import DATABASE_URL
from app.models.base.sqlalchemy_base import Base


def get_async_database_url() -> str:
    """Return DATABASE_URL with asyncpg driver for async engine."""
    if DATABASE_URL.startswith("postgresql://"):
        return DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        return DATABASE_URL
    return DATABASE_URL


# Async engine and session factory (used by versioned API when set on app.state)
_async_engine = None
_async_session_factory = None


def init_async_db():
    """Create async engine and session factory. Call once at app startup."""
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        return _async_session_factory
    url = get_async_database_url()
    _async_engine = create_async_engine(
        url,
        pool_pre_ping=True,
        echo=False,
    )
    _async_session_factory = async_sessionmaker(
        _async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return _async_session_factory


async def dispose_async_db():
    """Dispose async engine. Call once at app shutdown."""
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None

# Import all models so Base.metadata knows about every table
from app.models.sqlalchemy import (  # noqa: F401
    Address,
    AuditLog,
    BallotToken,
    BiometricChallenge,
    DeviceCredential,
    Candidate,
    Constituency,
    Election,
    ElectionOfficial,
    ErrorReport,
    Investigation,
    SeatAllocation,
    TallyResult,
    Voter,
    VoterLedger,
    Vote,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # set True for SQL logging during development
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables in the database. Safe to call multiple times (idempotent)."""
    Base.metadata.create_all(bind=engine)
