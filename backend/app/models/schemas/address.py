# address.py - Address schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field
from app.models.sqlalchemy.address import AddressType, AddressStatus
from datetime import datetime
from uuid import UUID
from typing import Optional

class AddressItem(ResponseSchema):
    """Address response model."""
    id: str = Field(..., description="The unique identifier for the address.")
    address_type: Optional[str] = Field(None, description="The type of address.")
    address_line1: Optional[str] = Field(None, description="The first line of the address.")
    address_line2: Optional[str] = Field(None, description="The second line of the address.")
    town: Optional[str] = Field(None, description="The town of the address.")
    postcode: Optional[str] = Field(None, description="The postcode of the address.")
    county: Optional[str] = Field(None, description="The county of the address.")
    country: Optional[str] = Field(None, description="The country of the address.")
    address_status: Optional[str] = Field(None, description="The status of the address.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the address needs to be renewed by.")

class CreateAddress(
    RequestSchema
):
    voter_id: UUID = Field(..., description="The unique identifier for the voter.")
    address_type: AddressType = Field(..., description="The type of address.")
    address_line1: str = Field(..., description="The first line of the address.")
    address_line2: str = Field(..., description="The second line of the address.")
    town: str = Field(..., description="The town of the address.")
    postcode: str = Field(..., description="The postcode of the address.")
    county: str = Field(..., description="The county of the address.")
    country: str = Field(..., description="The country of the address.")
    address_status: AddressStatus = Field(..., description="The status of the address.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the address needs to be renewed by. Auto-set to 2 years if not provided.")

class UpdateAddress(
    RequestSchema
):
    address_type: Optional[AddressType] = Field(None, description="The type of address.")
    address_line1: Optional[str] = Field(None, description="The first line of the address.")
    address_line2: Optional[str] = Field(None, description="The second line of the address.")
    town: Optional[str] = Field(None, description="The town of the address.")
    postcode: Optional[str] = Field(None, description="The postcode of the address.")
    county: Optional[str] = Field(None, description="The county of the address.")
    country: Optional[str] = Field(None, description="The country of the address.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the address needs to be renewed by.")
    address_status: Optional[AddressStatus] = Field(None, description="The status of the address.")

class DeleteAddress(
    RequestSchema
):
    address_id: UUID = Field(..., description="The unique identifier for the address.")