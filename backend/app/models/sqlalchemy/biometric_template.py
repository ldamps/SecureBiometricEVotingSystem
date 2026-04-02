"""Biometric template model - stored template per voter/modality."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, SmallInteger, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, UUIDPrimaryKeyMixin


class BiometricTemplate(Base, UUIDPrimaryKeyMixin):
    """Biometric template (e.g. fingerprint/face) for a voter."""

    __tablename__ = "biometric_template"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modality: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    template_data: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    template_dimension: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    encoded_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships ----------
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="biometric_templates",
        lazy="select",
    )

    # Database constraints + indexes ----------