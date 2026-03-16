# address.py - DTOs for address related operations

from dataclasses import dataclass
from typing import ClassVar
from app.application.constants import Resource
from uuid import UUID
from datetime import datetime
from app.models.sqlalchemy.address import AddressType, AddressStatus
from app.models.schemas.address import CreateAddress


@dataclass
class AddressBaseDTO:
    __resource__: ClassVar[Resource] = Resource.ADDRESS
    __encrypted_fields__: ClassVar[list[str]] = [
        "address_line1",
        "address_line2",
        "town",
        "postcode",
        "county",
        "country",
    ]

@dataclass
class AddressDTO(AddressBaseDTO):
    id: UUID
    voter_id: UUID
    address_type: AddressType
    address_line1: str
    address_line2: str
    town: str
    postcode: str
    county: str
    country: str
    address_status: AddressStatus
    created_at: datetime
    updated_at: datetime
    renew_by: datetime

@dataclass
class CreateAddressDTO(AddressBaseDTO):
    """Plaintext fields provided by the client/API."""
    voter_id: UUID
    address_type: AddressType
    address_line1: str
    address_line2: str
    town: str
    postcode: str
    county: str
    country: str
    renew_by: datetime

    @classmethod
    def create_dto(cls, model: CreateAddress, voter_id: UUID):
        return cls(
            **model.model_dump(),
            voter_id=voter_id,
        )

@dataclass
class CreateAddressEncryptedDTO(AddressBaseDTO):
    """Encrypted fields provided by the client/API."""
    pass


@dataclass
class DeleteAddressDTO():
    """DTO for deleting an address."""
    address_id: UUID
    voter_id: UUID
