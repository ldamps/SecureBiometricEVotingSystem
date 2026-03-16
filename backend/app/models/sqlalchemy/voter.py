# voter.py - Voter model for the e-voting system.

from __future__ import annotations

import uuid
from datetime import datetime
import enum
from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, TIMESTAMP, func, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedBytes, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqlalchemy.address import Address
from app.models.sqlalchemy.biometric_template import BiometricTemplate
from app.models.sqlalchemy.voter_ledger import VoterLedger
from app.models.sqlalchemy.constituency import Constituency

class VoterStatus(str, enum.Enum):
    """
    Voter status.
    ** PENDING ** - Voter has not been verified.
    ** SUSPENDED ** - Voter has been suspended due to too many failed authentication attempts.
    ** ACTIVE ** - Voter is active and can vote.
    """
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"
    ACTIVE = "ACTIVE"

class Voter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered voter with encrypted PII and constituency."""

    __tablename__ = "voter"

    national_insurance_number: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    passport_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    passport_country: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    surname: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    previous_first_name: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    previous_surname: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    date_of_birth: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)
    email: Mapped[bytes | None] = mapped_column(EncryptedBytes, nullable=True)  # UK in ER
    voter_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    voter_status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    constituency_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("constituency.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    registration_status: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    failed_auth_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    registered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    renew_by: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    
    # RELATIONSHIPS ----------

    # voter -> address (one voter can have multiple addresses i.g. current + previous)
    addresses: Mapped[list["Address"]] = relationship(
        "Address",
        back_populates="voter",
        cascade="all, delete-orphan",
    )
    
    # voter -> biometric template (one voter can have ...)
    biometric_templates: Mapped[list["BiometricTemplate"]] = relationship(
        "BiometricTemplate",
        back_populates="voter",
        cascade="all, delete-orphan",
    )

    # voter -> voter ledger (one voter can have multiple voter ledgers i.g. one for each election)
    voter_ledger: Mapped["VoterLedger"] = relationship(
        "VoterLedger",
        back_populates="voter",
        cascade="all, delete-orphan",
    )
    # voter -> constituency (one voter can only be registered in one constituency)
    constituency: Mapped["Constituency"] = relationship(
        "Constituency",
        back_populates="voters",
        cascade="all, delete-orphan",
    )
    # DATABASE CONSTRAINTS + INDEXES ----------
    __table_args__ = (
        
        CheckConstraint(
            # prevent negative failed auth attempts
            "failed_auth_attempts >= 0",
            name="ck_voter_failed_auth_attempts_positive",
        ),

        CheckConstraint(
            # Allow list of valid registration statuses (pending, approved, rejected)
            "registration_status IN ('pending', 'approved', 'rejected')",
            name="ck_voter_registration_status_valid",
        ),

        UniqueConstraint(
            # national insurance number must be unique
            "national_insurance_number",
            name="uq_voter_national_insurance_number_unique",
        ),

        UniqueConstraint(
            # voter reference must be unique
            "voter_reference",
            name="uq_voter_voter_reference_unique",
        ),
    )
