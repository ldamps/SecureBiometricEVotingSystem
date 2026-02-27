"""Base config for Pydantic schemas used with SQLAlchemy models."""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base config for Pydantic schemas used with SQLAlchemy models."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    