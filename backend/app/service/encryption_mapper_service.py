from __future__ import annotations

import dataclasses
from typing import Any, Optional, Type, TypeVar

import structlog

from app.infra.encryption.base import EncryptionPurpose
from app.models.base.sqlalchemy_base import EncryptedDBField
from app.service.encryption_service import EncryptionArgs, EncryptionService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()

PlainDTO = TypeVar("PlainDTO")
EncryptedDTO = TypeVar("EncryptedDTO")


class EncryptionMapperService:
    """Maps between plain DTOs and ORM models that use EncryptedColumn fields.

    Encrypt path
    ------------
    Takes a plain dataclass DTO and a target encrypted DTO class.  For every
    field name listed in the DTO's ``__encrypted_fields__`` class variable:
      - Encrypts the value using the DATABASE DEK.
      - If the model class also declares a ``<field>_search_token`` attribute,
        attaches a HMAC blind-index token using the SEARCH DEK.
    Returns an instance of the encrypted DTO class with EncryptedDBField values.

    Decrypt path
    ------------
    Takes a SQLAlchemy ORM model instance (whose EncryptedColumn attributes
    hold EncryptedDBField values) and a plain DTO class.  For every field in
    ``__encrypted_fields__``, decrypts the value and returns a populated plain DTO.
    """

    def __init__(
        self,
        encryption_service: EncryptionService,
        keys_manager: KeysManagerService,
    ) -> None:
        self._enc = encryption_service
        self._keys = keys_manager

    # ------------------------------------------------------------------ #
    #  Single-value helpers                                                #
    # ------------------------------------------------------------------ #

    async def encrypt_value(
        self,
        value: str,
        args: EncryptionArgs,
        session: Any,
        with_search_token: bool = False,
    ) -> EncryptedDBField:
        """Encrypt a single string value, optionally generating a search token."""
        db_dek, version = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.DATABASE, args.current_dek_version
        )
        search_dek: Optional[bytes] = None
        if with_search_token:
            search_dek, _ = await self._keys.get_dek(
                session, args.org_id, EncryptionPurpose.SEARCH, args.current_dek_version
            )
        return self._enc.encrypt_field(value, db_dek, version, search_dek=search_dek)

    async def decrypt_value(
        self,
        field: EncryptedDBField,
        args: EncryptionArgs,
        session: Any,
    ) -> str:
        """Decrypt a single EncryptedDBField."""
        db_dek, _ = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.DATABASE, field.dek_version
        )
        return self._enc.decrypt_field(field, db_dek)

    async def create_search_token(
        self,
        value: str,
        args: EncryptionArgs,
        session: Any,
    ) -> str:
        """Compute an HMAC-SHA256 blind index using the SEARCH DEK."""
        search_dek, _ = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.SEARCH, args.current_dek_version
        )
        return self._enc.create_search_token(value, search_dek)

    # ------------------------------------------------------------------ #
    #  DTO-level encrypt / decrypt                                         #
    # ------------------------------------------------------------------ #

    async def encrypt_dto(
        self,
        plain_dto: Any,
        encrypted_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Encrypt all ``__encrypted_fields__`` on *plain_dto*.

        Returns an instance of *encrypted_dto_class* where every encrypted
        field is an EncryptedDBField and every non-encrypted field is copied
        as-is.  If the encrypted DTO class has a ``<field>_search_token``
        attribute the token is populated automatically.
        """
        db_dek, version = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.DATABASE, args.current_dek_version
        )
        search_dek, _ = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.SEARCH, args.current_dek_version
        )

        encrypted_field_names: set[str] = set(
            getattr(plain_dto, "__encrypted_fields__", [])
        )
        encrypted_dto_fields = {f.name for f in dataclasses.fields(encrypted_dto_class)}

        kwargs: dict[str, Any] = {}

        for field in dataclasses.fields(plain_dto):
            name = field.name
            value = getattr(plain_dto, name)

            if name in encrypted_field_names and value is not None:
                str_value = str(value)
                # Check if the encrypted DTO wants a search token for this field
                token_attr = f"{name}_search_token"
                needs_token = token_attr in encrypted_dto_fields
                encrypted = self._enc.encrypt_field(
                    str_value, db_dek, version,
                    search_dek=search_dek if needs_token else None,
                )
                kwargs[name] = encrypted
                if needs_token:
                    kwargs[token_attr] = encrypted.search_token
            else:
                if name in encrypted_dto_fields:
                    kwargs[name] = value

        return encrypted_dto_class(**kwargs)

    async def decrypt_model(
        self,
        orm_model: Any,
        plain_dto_class: type,
        args: EncryptionArgs,
        session: Any,
    ) -> Any:
        """Decrypt all encrypted fields on *orm_model* and return a plain DTO.

        Fields listed in ``__encrypted_fields__`` that are EncryptedDBField
        instances are decrypted.  All other attributes are copied as-is if
        they exist on the plain DTO class.
        """
        encrypted_field_names: set[str] = set(
            getattr(plain_dto_class, "__encrypted_fields__", [])
        )
        plain_dto_fields = {f.name for f in dataclasses.fields(plain_dto_class)}

        kwargs: dict[str, Any] = {}

        for name in plain_dto_fields:
            raw = getattr(orm_model, name, None)
            if name in encrypted_field_names:
                if raw is None:
                    kwargs[name] = None
                elif isinstance(raw, dict):
                    raw = EncryptedDBField.from_dict(raw)
                    db_dek, _ = await self._keys.get_dek(
                        session, args.org_id, EncryptionPurpose.DATABASE, raw.dek_version
                    )
                    kwargs[name] = self._enc.decrypt_field(raw, db_dek)
                elif isinstance(raw, EncryptedDBField):
                    db_dek, _ = await self._keys.get_dek(
                        session, args.org_id, EncryptionPurpose.DATABASE, raw.dek_version
                    )
                    kwargs[name] = self._enc.decrypt_field(raw, db_dek)
                elif isinstance(raw, str):
                    kwargs[name] = raw
                elif isinstance(raw, (bytes, bytearray)):
                    kwargs[name] = raw.decode("utf-8", errors="replace") if raw else None
                else:
                    kwargs[name] = None
            else:
                kwargs[name] = raw

        return plain_dto_class(**kwargs)

    # ------------------------------------------------------------------ #
    #  Stream helpers                                                      #
    # ------------------------------------------------------------------ #

    async def encrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Encrypt a binary blob using the STORAGE DEK."""
        storage_dek, version = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.STORAGE, args.current_dek_version
        )
        return self._enc.encrypt_stream(data, storage_dek, version)

    async def decrypt_stream(
        self,
        data: bytes,
        args: EncryptionArgs,
        session: Any,
    ) -> bytes:
        """Decrypt a blob produced by encrypt_stream.

        The dek_version is read from the embedded JSON header so the correct
        historical DEK is fetched automatically.
        """
        import json, struct
        (header_len,) = struct.unpack(">I", data[:4])
        header = json.loads(data[4 : 4 + header_len])
        dek_version = header.get("dek_version", args.current_dek_version)

        storage_dek, _ = await self._keys.get_dek(
            session, args.org_id, EncryptionPurpose.STORAGE, dek_version
        )
        return self._enc.decrypt_stream(data, storage_dek)
