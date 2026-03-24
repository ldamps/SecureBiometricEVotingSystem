# address.py - Address model for the e-voting system.

from __future__ import annotations
import enum
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Enum as SAEnum, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter import Voter


class AddressType(str, enum.Enum):
    """ Address Type """
    OVERSEAS = "OVERSEAS" # Overseas address
    LOCAL_CURRENT = "LOCAL_CURRENT" # Current local address
    PAST = "PAST" # Past local address needed for those overseas

class AddressStatus(str, enum.Enum):
    """ Address Status """
    PENDING = "PENDING" # Address is pending verification
    ACTIVE = "ACTIVE" # Address is active (has been verified)
    REJECTED = "REJECTED" # Address is rejected

class Address(Base, UUIDPrimaryKeyMixin):
    """
    Read/Write Address for the e-voting system.
    All address fields are stored as EncryptedDBField (JSONB).
    Postcode has a companion search token for lookup without decryption.
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

    # Encrypted address fields
    address_line1: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    address_line2: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    town: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    postcode: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    postcode_search_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    county: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    country: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)

    # Non-encrypted fields
    address_status: Mapped[AddressStatus] = mapped_column(
        SAEnum(AddressStatus, name="address_status_enum", create_constraint=True),
        nullable=False,
        index=True,
    )
    renew_by: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # RELATIONSHIPS ----------

    voter: Mapped["Voter"] = relationship(
        "Voter",
        back_populates="addresses",
        lazy="select",
    )

    # Database constraints + indexes ----------
    __table_args__ = (

    )
