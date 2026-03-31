# app/models/dto/official.py - DTOs for election official operations.

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.schemas.official import OfficialItem, CreateOfficialRequest, UpdateOfficialRequest
from app.models.sqlalchemy.election_official import ElectionOfficial, OfficialRole


@dataclass
class OfficialBaseDTO:
    """Base DTO for election officials."""
    __resource__: ClassVar[Resource] = Resource.OFFICIAL
    __encrypted_fields__: ClassVar[list[str]] = ["first_name", "last_name", "email_hash"]


@dataclass
class OfficialDTO(OfficialBaseDTO):
    """Plaintext official DTO — target for decrypt_model and source for to_schema."""

    id: UUID = None
    username: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: str = ""
    is_active: bool = True
    must_reset_password: bool = False
    failed_login_attempts: int = 0
    created_by: Optional[UUID] = None
    last_login_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None

    def to_schema(self) -> OfficialItem:
        return OfficialItem(
            id=str(self.id),
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            role=self.role,
            is_active=self.is_active,
            must_reset_password=self.must_reset_password,
            failed_login_attempts=self.failed_login_attempts,
            created_by=str(self.created_by) if self.created_by else None,
            last_login_at=self.last_login_at,
            locked_until=self.locked_until,
        )


@dataclass
class CreateOfficialPlainDTO(OfficialBaseDTO):
    """Plaintext fields for creating an election official."""

    username: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password: str = ""
    role: str = ""
    created_by: Optional[UUID] = None

    @classmethod
    def create_dto(cls, data: CreateOfficialRequest) -> "CreateOfficialPlainDTO":
        d = data.model_dump()
        d["role"] = d["role"].value if isinstance(d["role"], OfficialRole) else d["role"]
        if d.get("created_by"):
            d["created_by"] = UUID(d["created_by"]) if isinstance(d["created_by"], str) else d["created_by"]
        return cls(**d)


@dataclass
class UpdateOfficialPlainDTO(OfficialBaseDTO):
    """Plaintext fields for updating an election official."""

    official_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @classmethod
    def create_dto(cls, data: UpdateOfficialRequest, official_id: UUID) -> "UpdateOfficialPlainDTO":
        d = data.model_dump(exclude_none=True)
        if "role" in d and isinstance(d["role"], OfficialRole):
            d["role"] = d["role"].value
        return cls(**d, official_id=official_id)
