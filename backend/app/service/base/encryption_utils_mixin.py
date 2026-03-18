from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

import structlog

from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.encryption_service import EncryptionArgs
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()

PlainDTO = TypeVar("PlainDTO")


class EncryptionUtilsMixin:
    """Mixin for domain services that need to encrypt/decrypt field data.

    Usage
    -----
    Inherit alongside your service class and inject the required dependencies:

        class VoterService(EncryptionUtilsMixin):
            def __init__(self, ..., mapper: EncryptionMapperService,
                         keys_manager: KeysManagerService):
                self._mapper = mapper
                self._keys_manager = keys_manager

    The mixin resolves the encryption context (system-level or org-scoped)
    and delegates to EncryptionMapperService for the actual crypto work.

    Typical create flow
    -------------------
        args  = await self._build_args(session, org=org)
        enc   = await self._encrypt_dto(plain_dto, EncryptedDTO, args, session)
        model = await repo.create(session, enc)
        return await self._decrypt_and_return(model, PlainDTO, args, session)

    Typical read flow
    -----------------
        model = await repo.get(session, id)
        return await self._decrypt_and_return(model, PlainDTO, args, session)
    """

    # Subclasses must assign these in their __init__
    _mapper: EncryptionMapperService
    _keys_manager: KeysManagerService

    # ------------------------------------------------------------------ #
    #  Context resolution                                                  #
    # ------------------------------------------------------------------ #

    async def _build_args(
        self,
        session: Any,
        org: Optional[Any] = None,
        system_key: bool = False,
    ) -> EncryptionArgs:
        """Resolve the EncryptionArgs for the current operation.

        Pass *org* (an object with a `.id` attribute or a raw UUID) for
        organisation-scoped encryption, or *system_key=True* for system-level
        keys (e.g. admin users, platform-wide data).
        """
        org_id = None
        if org is not None:
            org_id = org.id if hasattr(org, "id") else org
        elif system_key:
            org_id = None  # system keys use org_id=NULL

        return await self._keys_manager.build_encryption_args(session, org_id=org_id)

    # ------------------------------------------------------------------ #
    #  DTO encryption / decryption                                         #
    # ------------------------------------------------------------------ #

    async def _encrypt_dto(
        self,
        plain_dto: Any,
        encrypted_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Encrypt all ``__encrypted_fields__`` on *plain_dto*.

        Returns an instance of *encrypted_dto_class* ready for persistence.
        """
        return await self._mapper.encrypt_dto(plain_dto, encrypted_dto_class, args, session)

    async def _decrypt_model(
        self,
        orm_model: Any,
        plain_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Decrypt all encrypted fields on *orm_model*, returning a plain DTO."""
        return await self._mapper.decrypt_model(orm_model, plain_dto_class, args, session)

    async def _decrypt_and_return(
        self,
        orm_model: Any,
        plain_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Decrypt *orm_model* into a plain DTO and call ``.to_schema()`` on it.

        Convenience wrapper for the common pattern:
            plain = await self._decrypt_model(model, DTO, args, session)
            return plain.to_schema()
        """
        plain = await self._decrypt_model(orm_model, plain_dto_class, args, session)
        return plain.to_schema()

    # ------------------------------------------------------------------ #
    #  Search tokens                                                       #
    # ------------------------------------------------------------------ #

    async def _get_search_token(
        self,
        value: str,
        args: EncryptionArgs,
        session: Any,
    ) -> str:
        """Return an HMAC-SHA256 blind index for querying an encrypted field."""
        return await self._mapper.create_search_token(value, args, session)

    # ------------------------------------------------------------------ #
    #  Stream (blob) encrypt / decrypt                                     #
    # ------------------------------------------------------------------ #

    async def _encrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Encrypt a binary blob using the STORAGE DEK."""
        return await self._mapper.encrypt_stream(data, args, session)

    async def _decrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Decrypt a blob produced by _encrypt_stream."""
        return await self._mapper.decrypt_stream(data, args, session)
