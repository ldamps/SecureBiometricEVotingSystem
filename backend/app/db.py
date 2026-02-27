"""Database engine, session, and dependency for FastAPI.

Use get_db() in route dependencies to get a session. Call create_tables()
once to create all tables (e.g. from a script or on first run); for ongoing
changes use Alembic migrations instead.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL
from app.models.base.sqlalchemy_base import Base

# Import all models so Base.metadata knows about every table
from app.models.sqlalchemy import (  # noqa: F401
    Address,
    AuditLog,
    BallotToken,
    BiometricTemplate,
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
