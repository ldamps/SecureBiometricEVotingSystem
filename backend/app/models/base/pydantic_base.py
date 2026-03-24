"""Base config for Pydantic schemas used with SQLAlchemy models."""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any
import uuid


class BaseSchema(BaseModel):
    """Base config for Pydantic schemas used with SQLAlchemy models."""

    model_config = ConfigDict(
        from_attributes=True,
    )

class ResponseSchema(BaseSchema):
    """
    Base for API response schemas that represent database entities
    Includes:
    - UUID to string conversion
    - Standard API response configuration
    """
    @field_validator("id", mode="before", check_fields=False)
    @classmethod
    def convert_uuid_to_string(cls, v: Any) -> str:
        """Convert UUID objects to strings."""
        if isinstance(v, uuid.UUID):
            return str(v)
        return str(v) if v is not None else v


class RequestSchema(BaseSchema):
    pass
