# address.py - Address schemas for the e-voting system.
from app.models.base.pydantic_base import ResponseSchema, RequestSchema
from pydantic import Field, field_validator, model_validator
from app.models.sqlalchemy.address import AddressType, AddressStatus
from app.utils.postcode_validator import is_valid_uk_postcode
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
    """Create address request.

    For OVERSEAS addresses, county and postcode are not required.
    For LOCAL_CURRENT and PAST addresses, county and postcode are mandatory.
    """
    address_type: AddressType = Field(..., description="The type of address.")
    address_line1: str = Field(..., description="The first line of the address.")
    address_line2: Optional[str] = Field(None, description="The second line of the address.")
    town: str = Field(..., description="The town of the address.")
    postcode: Optional[str] = Field(None, description="The postcode of the address. Required for local addresses.")
    county: Optional[str] = Field(None, description="The county of the address. Required for local addresses.")
    country: str = Field(..., description="The country of the address.")
    renew_by: Optional[datetime] = Field(None, description="The date and time the address needs to be renewed by. Auto-set to 2 years if not provided.")

    @model_validator(mode="after")
    def require_county_postcode_for_local(self) -> "CreateAddress":
        """County and postcode are required for local addresses but not overseas.
        UK postcodes are validated for correct format.
        """
        if self.address_type != AddressType.OVERSEAS:
            if not self.county or not self.county.strip():
                raise ValueError("County is required for local addresses.")
            if not self.postcode or not self.postcode.strip():
                raise ValueError("Postcode is required for local addresses.")
            if not is_valid_uk_postcode(self.postcode):
                raise ValueError(
                    f"'{self.postcode}' is not a valid UK postcode. "
                    "Expected format: e.g. SW1A 1AA, M1 1AE, B33 8TH."
                )
        return self

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