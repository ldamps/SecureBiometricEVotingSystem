"""Base config for Pydantic schemas used with SQLAlchemy models."""

from pydantic import ConfigDict

# Use when schema is built from an ORM model (e.g. response schemas)
ORM_CONFIG = ConfigDict(from_attributes=True, populate_by_name=True)
