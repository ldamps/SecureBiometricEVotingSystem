"""Referendum model - a standalone yes/no question posed to voters."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Referendum(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A standalone yes/no referendum question presented to voters."""

    __tablename__ = "referendum"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="OPEN", index=True)
    voting_opens: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    voting_closes: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
