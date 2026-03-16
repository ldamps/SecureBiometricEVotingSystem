from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import LargeBinary, MetaData, inspect, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

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

# Encrypted Column Type ----------


class EncryptedBytes(TypeDecorator):
    """Stores encrypted binary data. Uses LargeBinary at DB level; encryption can be applied in app layer."""

    impl = LargeBinary
    cache_ok = True


__all__ = {
    "Base",
    "UUIDPrimaryKeyMixin",
    "CreatedAtMixin",
    "TimestampMixin",
    "EncryptedBytes",
    "NAMING_CONVENTION",
}
