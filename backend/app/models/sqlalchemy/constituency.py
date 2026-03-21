"""Constituency model - electoral area.

Each constituency represents a ceremonial county in the UK.
Constituencies are seeded from a fixed list and are read-only at the
application level (no create / update / delete endpoints).
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class Constituency(Base, UUIDPrimaryKeyMixin):
    """Electoral constituency mapped to a UK county."""

    __tablename__ = "constituency"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    county: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships ----------
    voters: Mapped[list["Voter"]] = relationship(
        "Voter",
        back_populates="constituency",
    )

    # Database constraints + indexes ----------