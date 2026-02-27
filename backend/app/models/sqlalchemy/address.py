"""Address model - voter address (encrypted)."""

from __future__ import annotations

import uuid
import enum
from sqlalchemy import ForeignKey, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedBytes


class AddressType(str, enum.Enum):
    """ Address Type """
    OVERSEAS = "OVERSEAS" # Overseas address
    LOCAL_CURRENT = "LOCAL_CURRENT" # Current local address
    LOCAL_PAST = "LOCAL_PAST" # Past local address needed for those overseas

class Address(Base):
    """ 
    Read/Write Address for the e-voting system. 
    """

    __tablename__ = "address"

    address_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.voter_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    address_type: Mapped[AddressType] = mapped_column(
        SAEnum(AddressType, name="address_type_enum", create_constraint=True),
        nullable=False,
        index=True,
    )
    address_line1: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    address_line2: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    town: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    postcode: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    county: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    country: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)

    # Relationships ----------

    # Database constraints + indexes ----------
