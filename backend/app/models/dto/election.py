# app/models/dto/election.py - DTOs for election related operations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.election import ElectionItem, CreateElectionRequest, UpdateElectionRequest
from app.models.sqlalchemy.election import Election, ElectionType, ElectionScope, ElectionStatus, AllocationMethod


@dataclass
class ElectionBaseDTO:
    """Base Data Transfer Object for elections."""
    __resource__: ClassVar[Resource] = Resource.ELECTION
    __encrypted_fields__: ClassVar[list[str]] = []


@dataclass
class ElectionDTO(ElectionBaseDTO):
    """Plaintext election DTO — target for decrypt_model and source for to_schema."""

    id: UUID
    title: str
    election_type: str
    scope: str
    allocation_method: str
    status: str
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    created_by: Optional[UUID] = None

    def to_schema(self) -> ElectionItem:
        return ElectionItem(
            id=str(self.id),
            title=self.title,
            election_type=self.election_type,
            scope=self.scope,
            allocation_method=self.allocation_method,
            status=self.status,
            voting_opens=self.voting_opens,
            voting_closes=self.voting_closes,
            created_by=str(self.created_by) if self.created_by else None,
        )


@dataclass
class CreateElectionPlainDTO(ElectionBaseDTO):
    """Plaintext fields for creating an election."""

    title: str = ""
    election_type: str = ""
    scope: str = ""
    allocation_method: str = ""
    status: str = ""
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    created_by: Optional[UUID] = None

    @classmethod
    def create_dto(cls, data: CreateElectionRequest) -> "CreateElectionPlainDTO":
        d = data.model_dump()
        d["election_type"] = d["election_type"].value if isinstance(d["election_type"], ElectionType) else d["election_type"]
        d["scope"] = d["scope"].value if isinstance(d["scope"], ElectionScope) else d["scope"]
        d["status"] = d["status"].value if isinstance(d["status"], ElectionStatus) else d["status"]
        if d.get("created_by"):
            d["created_by"] = UUID(d["created_by"]) if isinstance(d["created_by"], str) else d["created_by"]
        return cls(**d)


@dataclass
class CreateElectionEncryptedDTO(ElectionBaseDTO):
    """Encrypted fields for persisting a new election row.

    Elections have no encrypted fields — this DTO simply mirrors
    the plain DTO so it can pass through the standard encrypt pipeline.
    """

    title: str = ""
    election_type: str = ""
    scope: str = ""
    allocation_method: str = ""
    status: str = ""
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None
    created_by: Optional[UUID] = None

    def to_model(self) -> Election:
        return Election(**asdict(self))


@dataclass
class UpdateElectionPlainDTO(ElectionBaseDTO):
    """Plaintext fields for updating an election.

    Only status, voting_opens, and voting_closes can be updated
    once an election has been created. All other fields are immutable.
    """

    election_id: Optional[UUID] = None
    status: Optional[str] = None
    voting_opens: Optional[datetime] = None
    voting_closes: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: UpdateElectionRequest, election_id: UUID) -> "UpdateElectionPlainDTO":
        d = data.model_dump(exclude_none=True)
        if "status" in d and isinstance(d["status"], ElectionStatus):
            d["status"] = d["status"].value
        return cls(**d, election_id=election_id)
