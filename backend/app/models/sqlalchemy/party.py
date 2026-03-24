# party.py - Party model for the e-voting system.

from __future__ import annotations

from sqlalchemy import String, Boolean, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import TYPE_CHECKING
from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin
from app.models.sqlalchemy.candidate import Candidate
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from app.models.sqlalchemy.candidate import Candidate

class Party(Base, UUIDPrimaryKeyMixin):
    """Party model for the e-voting system."""

    __tablename__ = "party"
    party_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    abbreviation: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships ----------
    candidates: Mapped[list["Candidate"]] = relationship(
        "Candidate",
        back_populates="party",
    )

    # Database constraints + indexes ----------
    __table_args__ = (
        UniqueConstraint(
            "party_name",
            name="uq_party_party_name",
        ),
    )






