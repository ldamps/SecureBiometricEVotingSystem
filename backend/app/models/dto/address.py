# app/models/dto/address.py - DTOs for address related operations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import ClassVar, Optional
from uuid import UUID

from app.application.constants import Resource
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.models.schemas.address import AddressItem, CreateAddress, UpdateAddress
from app.models.sqlalchemy.address import Address, AddressType, AddressStatus


@dataclass
class AddressBaseDTO:
    """Base Data Transfer Object for addresses."""
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
    """Plaintext address DTO — target for decrypt_model and source for to_schema."""
    id: UUID = None
    voter_id: UUID = None
    address_type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    town: Optional[str] = None
    postcode: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None
    address_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_schema(self) -> AddressItem:
        return AddressItem(
            id=str(self.id),
            address_type=self.address_type,
            address_line1=self.address_line1,
            address_line2=self.address_line2,
            town=self.town,
            postcode=self.postcode,
            county=self.county,
            country=self.country,
            address_status=self.address_status,
        )


@dataclass
class CreateAddressPlainDTO(AddressBaseDTO):
    """Plaintext fields provided by the client for address creation."""
    voter_id: Optional[UUID] = None
    address_type: Optional[str] = None
    address_line1: str = ""
    address_line2: str = ""
    town: str = ""
    postcode: str = ""
    county: str = ""
    country: str = ""
    address_status: str = "PENDING"
    renew_by: Optional[datetime] = None

    @classmethod
    def create_dto(cls, data: CreateAddress) -> "CreateAddressPlainDTO":
        return cls(**data.model_dump())



@dataclass
class CreateAddressEncryptedDTO(AddressBaseDTO):
    """Encrypted fields for persisting a new address row."""
    voter_id: Optional[UUID] = None
    address_type: Optional[str] = None
    address_status: str = "PENDING"
    address_line1: Optional[EncryptedDBField] = None
    address_line2: Optional[EncryptedDBField] = None
    town: Optional[EncryptedDBField] = None
    postcode: Optional[EncryptedDBField] = None
    postcode_search_token: Optional[str] = None
    county: Optional[EncryptedDBField] = None
    country: Optional[EncryptedDBField] = None

    def to_model(self) -> Address:
        return Address(**asdict(self))


@dataclass
class UpdateAddressPlainDTO(AddressBaseDTO):
    """Plaintext fields for updating an address."""
    address_id: Optional[UUID] = None
    voter_id: Optional[UUID] = None
    address_type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    town: Optional[str] = None
    postcode: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None
    address_status: Optional[str] = None


@dataclass
class UpdateAddressEncryptedDTO(AddressBaseDTO):
    """Encrypted fields for updating an address row."""
    address_id: Optional[UUID] = None
    voter_id: Optional[UUID] = None
    address_type: Optional[str] = None
    address_status: Optional[str] = None
    address_line1: Optional[EncryptedDBField] = None
    address_line2: Optional[EncryptedDBField] = None
    town: Optional[EncryptedDBField] = None
    postcode: Optional[EncryptedDBField] = None
    postcode_search_token: Optional[str] = None
    county: Optional[EncryptedDBField] = None
    country: Optional[EncryptedDBField] = None


@dataclass
class DeleteAddressDTO:
    """DTO for deleting an address."""
    address_id: UUID = None
    voter_id: UUID = None
