"""Constituency model - electoral area."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, UUIDPrimaryKeyMixin


class Constituency(Base, UUIDPrimaryKeyMixin):
    """Electoral constituency (area)."""

    __tablename__ = "constituency"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    county: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships ----------

    # Database constraints + indexes ----------