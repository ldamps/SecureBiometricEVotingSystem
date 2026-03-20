# voter.py - Voter model for the e-voting system.

from __future__ import annotations

import uuid
from datetime import datetime
import enum
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base.sqlalchemy_base import Base, EncryptedColumn, EncryptedDBField, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.sqlalchemy.address import Address
from app.models.sqlalchemy.biometric_template import BiometricTemplate
from app.models.sqlalchemy.voter_ledger import VoterLedger
from app.models.sqlalchemy.constituency import Constituency

if TYPE_CHECKING:
    from app.models.sqlalchemy.voter_passport import VoterPassport


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


class NationalityCategory(str, enum.Enum):
    """Nationality category that determines voting eligibility.

    UK electoral law grants voting rights based on nationality/immigration
    status, not just residency.  This enum captures the broad categories.
    """
    BRITISH_CITIZEN = "BRITISH_CITIZEN"
    IRISH_CITIZEN = "IRISH_CITIZEN"
    COMMONWEALTH_SETTLED = "COMMONWEALTH_SETTLED"
    COMMONWEALTH_LEAVE_TO_REMAIN = "COMMONWEALTH_LEAVE_TO_REMAIN"
    EU_RETAINED_RIGHTS = "EU_RETAINED_RIGHTS"
    OTHER = "OTHER"


class ImmigrationStatus(str, enum.Enum):
    """Recorded immigration status for non-British voters.

    The system records the claimed status; actual verification is
    performed externally by electoral registration officers.
    """
    INDEFINITE_LEAVE_TO_REMAIN = "INDEFINITE_LEAVE_TO_REMAIN"
    LIMITED_LEAVE_TO_REMAIN = "LIMITED_LEAVE_TO_REMAIN"
    PRE_SETTLED_STATUS = "PRE_SETTLED_STATUS"
    SETTLED_STATUS = "SETTLED_STATUS"
    EXEMPT = "EXEMPT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Voter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered voter with encrypted PII and constituency.

    All personally-identifiable fields are stored as EncryptedDBField (JSONB).
    Searchable fields have a companion ``*_search_token`` column (HMAC-SHA256
    hex digest) so queries can locate rows without decrypting field values.
    Unique constraints are placed on the search token columns, not the
    encrypted columns, so database-level deduplication still works.
    """

    __tablename__ = "voter"

    # ------------------------------------------------------------------ #
    #  Encrypted PII fields                                                #
    # ------------------------------------------------------------------ #

    national_insurance_number: Mapped[EncryptedDBField | None] = mapped_column(
        EncryptedColumn, nullable=True
    )
    # Blind-index for uniqueness / lookup without decryption
    national_insurance_number_search_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    first_name: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    surname: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    previous_first_name: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    previous_surname: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    date_of_birth: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)

    email: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    email_search_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    voter_reference: Mapped[EncryptedDBField | None] = mapped_column(EncryptedColumn, nullable=True)
    voter_reference_search_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )

    # ------------------------------------------------------------------ #
    #  Non-encrypted fields                                                #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    #  Nationality & immigration status                                    #
    # ------------------------------------------------------------------ #

    nationality_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    immigration_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    immigration_status_expiry: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # RELATIONSHIPS ----------

    addresses: Mapped[list["Address"]] = relationship(
        "Address",
        back_populates="voter",
        cascade="all, delete-orphan",
    )

    passports: Mapped[list["VoterPassport"]] = relationship(
        "VoterPassport",
        back_populates="voter",
        cascade="all, delete-orphan",
    )

    biometric_templates: Mapped[list["BiometricTemplate"]] = relationship(
        "BiometricTemplate",
        back_populates="voter",
        cascade="all, delete-orphan",
    )

    voter_ledger: Mapped["VoterLedger"] = relationship(
        "VoterLedger",
        back_populates="voter",
        cascade="all, delete-orphan",
    )

    constituency: Mapped["Constituency"] = relationship(
        "Constituency",
        back_populates="voters",
    )

    # DATABASE CONSTRAINTS + INDEXES ----------
    __table_args__ = (
        CheckConstraint(
            "failed_auth_attempts >= 0",
            name="ck_voter_failed_auth_attempts_positive",
        ),
        CheckConstraint(
            "registration_status IN ('pending', 'approved', 'rejected')",
            name="ck_voter_registration_status_valid",
        ),
        CheckConstraint(
            "nationality_category IN ("
            "'BRITISH_CITIZEN', 'IRISH_CITIZEN', 'COMMONWEALTH_SETTLED', "
            "'COMMONWEALTH_LEAVE_TO_REMAIN', 'EU_RETAINED_RIGHTS', 'OTHER')",
            name="ck_voter_nationality_category_valid",
        ),
        # Uniqueness is enforced on search tokens (hex HMAC), not on the
        # encrypted JSONB columns.
        UniqueConstraint(
            "national_insurance_number_search_token",
            name="uq_voter_national_insurance_number_search_token",
        ),
        UniqueConstraint(
            "voter_reference_search_token",
            name="uq_voter_voter_reference_search_token",
        ),
    )
