# app/models/dto/auth.py - DTOs for authentication operations.

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class TokenPayload:
    """Decoded JWT token payload."""
    sub: str          # official ID (string UUID)
    username: str
    role: str
    token_type: str   # "access" or "refresh"
    exp: int          # expiry timestamp
    iat: int          # issued-at timestamp
