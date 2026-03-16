# address.py - Address model for the e-voting system.

from __future__ import annotations
import enum
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Enum as SAEnum, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base.sqlalchemy_base import Base, EncryptedBytes, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter import Voter


class AddressType(str, enum.Enum):
    """ Address Type """
    OVERSEAS = "OVERSEAS" # Overseas address
    LOCAL_CURRENT = "LOCAL_CURRENT" # Current local address
    LOCAL_PAST = "LOCAL_PAST" # Past local address needed for those overseas

class AddressStatus(str, enum.Enum):
    """ Address Status """
    PENDING = "PENDING" # Address is pending verification
    ACTIVE = "ACTIVE" # Address is active (has been verified)
    REJECTED = "REJECTED" # Address is rejected

class Address(Base, UUIDPrimaryKeyMixin):
    """ 
    Read/Write Address for the e-voting system. 
    """

    __tablename__ = "address"

    voter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("voter.id", ondelete="CASCADE"),
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
    address_status: Mapped[AddressStatus] = mapped_column(
        SAEnum(AddressStatus, name="address_status_enum", create_constraint=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # RELATIONSHIPS ----------

    # voter -> address (one voter can have multiple addresses e.g. current + previous)
    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="addresses",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Database constraints + indexes ----------
    __table_args__ = (

    )
