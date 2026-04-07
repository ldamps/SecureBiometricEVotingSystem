from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import LargeBinary, MetaData, inspect, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

# Alembic-friendly naming conventions
NAMING_CONVENTION = {
    # Ensures index names are deterministic so Alembic can autogenerate
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Base Class ----------
class Base(DeclarativeBase):
    """Root declarative base for all SQLAlchemy models."""

    metadata = MetaData(schema="public", naming_convention=NAMING_CONVENTION)

    def to_dict(self) -> Dict[str, Any]:
        insp = inspect(self)
        data: Dict[str, Any] = {}
        for attr in insp.mapper.column_attrs:
            key = attr.key
            value = getattr(self, key)
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                data[key] = str(value)
            else:
                data[key] = value
        return data

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"<{self.__class__.__name__} {fields}>"


# Mixins ----------
class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named `id` (defaults to uuid4)."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class CreatedAtMixin:
    """Adds created_at column (always UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("utc", func.now()),
    )

class TimestampMixin(CreatedAtMixin):
    """Adds created_at and updated_at columns (always UTC) - Production grade."""

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("utc", func.now()),
        onupdate=func.timezone("utc", func.now()),
    )

# Encrypted Column Types ----------


class EncryptedBytes(TypeDecorator):
    """Legacy: stores encrypted binary data as LargeBinary. Kept for backward compatibility."""

    impl = LargeBinary
    cache_ok = True


@dataclass
class EncryptedDBField:
    """Structured encrypted value stored as JSONB.

    All binary values are lowercase hex strings.
    The GCM tag (16 bytes) is stored separately from the ciphertext so the
    wire format is explicit and easy to audit.
    """

    ciphertext: str            # hex — raw ciphertext (excludes GCM tag)
    nonce: str                 # hex — 12-byte AES-GCM nonce
    tag: str                   # hex — 16-byte AES-GCM authentication tag
    dek_version: int           # which DEK version was used
    search_token: Optional[str] = None  # hex — HMAC-SHA256 blind index (searchable fields only)

    def to_dict(self) -> dict:
        d = {
            "ciphertext": self.ciphertext,
            "nonce": self.nonce,
            "tag": self.tag,
            "dek_version": self.dek_version,
        }
        if self.search_token is not None:
            d["search_token"] = self.search_token
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptedDBField":
        return cls(
            ciphertext=data["ciphertext"],
            nonce=data["nonce"],
            tag=data["tag"],
            dek_version=data["dek_version"],
            search_token=data.get("search_token"),
        )


class EncryptedColumn(TypeDecorator):
    """SQLAlchemy TypeDecorator that stores an EncryptedDBField (or a list of them) as JSONB.

    Usage in a model:
        field: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return [v.to_dict() if isinstance(v, EncryptedDBField) else v for v in value]
        if isinstance(value, EncryptedDBField):
            return value.to_dict()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return [
                EncryptedDBField.from_dict(v)
                if isinstance(v, dict) and "ciphertext" in v
                else v
                for v in value
            ]
        if isinstance(value, dict):
            if "ciphertext" not in value:
                return value
            return EncryptedDBField.from_dict(value)
        return value


__all__ = {
    "Base",
    "UUIDPrimaryKeyMixin",
    "CreatedAtMixin",
    "TimestampMixin",
    "EncryptedBytes",
    "EncryptedDBField",
    "EncryptedColumn",
    "NAMING_CONVENTION",
}
