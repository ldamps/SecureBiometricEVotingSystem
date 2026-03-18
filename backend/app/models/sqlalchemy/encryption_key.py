from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base.sqlalchemy_base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EncryptionKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores encrypted Data Encryption Keys (DEKs) per organisation and purpose.

    The raw DEK is never persisted. Only the KMS-encrypted form is stored here.
    At runtime the DEK is decrypted on demand via the KMS Key Encryption Key (KEK).

    One active row per (org_id, purpose) at any time.  On rotation the old row
    is deactivated (is_active=False) and a new row is inserted with version+1.
    System-level keys use org_id=NULL.
    """

    __tablename__ = "encryption_key"

    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    encrypted_dek: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    kms_key_id: Mapped[str] = mapped_column(String(512), nullable=False)
    kms_key_region: Mapped[str] = mapped_column(String(64), nullable=False, default="us-east-1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "org_id", "purpose", "version",
            name="uq_encryption_key_org_purpose_version",
        ),
    )
