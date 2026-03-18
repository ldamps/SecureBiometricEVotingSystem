from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class EncryptionKeyDTO:
    """Read DTO for a persisted DEK record."""

    id: uuid.UUID
    org_id: Optional[uuid.UUID]
    purpose: str
    version: int
    encrypted_dek: bytes
    kms_key_id: str
    kms_key_region: str
    is_active: bool


@dataclass
class CreateEncryptionKeyDTO:
    """DTO used when storing a newly generated DEK."""

    org_id: Optional[uuid.UUID]
    purpose: str
    version: int
    encrypted_dek: bytes
    kms_key_id: str
    kms_key_region: str
