"""Create all tables from SQLAlchemy models.

Revision ID: 001
Revises:
Create Date: 2025-02-25

"""
from typing import Sequence, Union

from alembic import op

from app.models.base.sqlalchemy_base import Base

# Import all models so Base.metadata is fully populated
from app.models.sqlalchemy import (  # noqa: F401
    Address,
    AuditLog,
    BallotToken,
    BiometricChallenge,
    Candidate,
    Constituency,
    DeviceCredential,
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

revision: str = "20250225_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
