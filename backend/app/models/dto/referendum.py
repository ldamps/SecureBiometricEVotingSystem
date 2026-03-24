# referendum_dto.py - Referendum DTOs for the e-voting system.

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.referendum import ReferendumItem, CreateReferendumRequest
from app.models.sqlalchemy.referendum import Referendum


@dataclass
class ReferendumBaseDTO:
    """Base Data Transfer Object for referendums."""
    __resource__: ClassVar[Resource] = Resource.REFERENDUM
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class ReferendumDTO(ReferendumBaseDTO):
    """Plaintext referendum DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    title: str = ""
    question: str = ""
    description: Optional[str] = None
    scope: str = ""
    status: str = "OPEN"
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    is_active: bool = True

    def to_schema(self) -> ReferendumItem:
        return ReferendumItem(
            id=str(self.id),
            title=self.title,
            question=self.question,
            description=self.description,
            scope=self.scope,
            status=self.status,
            voting_opens=self.voting_opens,
            voting_closes=self.voting_closes,
            is_active=self.is_active,
        )


@dataclass
class CreateReferendumPlainDTO(ReferendumBaseDTO):
    """Plaintext fields for creating a referendum."""

    title: str = ""
    question: str = ""
    description: Optional[str] = None
    scope: str = ""
    status: str = "OPEN"
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: CreateReferendumRequest) -> "CreateReferendumPlainDTO":
        return cls(
            title=data.title,
            question=data.question,
            description=data.description,
            scope=data.scope,
            status=data.status or "OPEN",
            voting_opens=data.voting_opens,
            voting_closes=data.voting_closes,
        )


@dataclass
class CreateReferendumEncryptedDTO(ReferendumBaseDTO):
    """Encrypted fields for persisting a new referendum row.

    Referendums have no encrypted fields — this DTO simply mirrors
    the plain DTO so it can pass through the standard encrypt pipeline.
    """

    title: str = ""
    question: str = ""
    description: Optional[str] = None
    scope: str = ""
    status: str = "OPEN"
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None

    def to_model(self) -> Referendum:
        return Referendum(**asdict(self))


@dataclass
class UpdateReferendumPlainDTO(ReferendumBaseDTO):
    """Plaintext fields for updating a referendum."""

    referendum_id: Optional[UUID] = None
    question: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    is_active: Optional[bool] = None
