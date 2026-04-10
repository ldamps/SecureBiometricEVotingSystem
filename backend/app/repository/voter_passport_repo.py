# voter_passport_repo.py - Repository layer for voter passport operations.

from dataclasses import asdict

from app.models.sqlalchemy.voter_passport import VoterPassport
from app.models.dto.voter_passport import UpdateVoterPassportPlainDTO
from typing import Type, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from app.application.core.exceptions import NotFoundError
import structlog

logger = structlog.get_logger()


class VoterPassportRepository:
    """Voter passport repository operations."""

    def __init__(self, model: Type[VoterPassport] = VoterPassport) -> None:
        self._model = model

    async def get_voter_id_by_passport_search_token(
        self,
        session: AsyncSession,
        token: str,
    ) -> UUID | None:
        """Return the voter_id that owns a passport with the given search token, or None."""
        result = await session.execute(
            select(self._model.voter_id).where(
                self._model.passport_number_search_token == token
            )
        )
        return result.scalar_one_or_none()

    async def create_passport(
        self,
        session: AsyncSession,
        passport: VoterPassport,
    ) -> VoterPassport:
        """Persist a new voter passport entry."""
        try:
            session.add(passport)
            await session.flush()
            logger.info(
                "Voter passport created successfully",
                passport_id=passport.id,
                voter_id=passport.voter_id,
            )
            return passport
        except Exception:
            logger.exception("Failed to create voter passport")
            raise

    async def get_passport_by_id(
        self,
        session: AsyncSession,
        passport_id: UUID,
    ) -> VoterPassport:
        """Get a passport entry by its ID."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.id == passport_id)
            )
            passport = result.scalar_one_or_none()
            if not passport:
                raise NotFoundError("Voter passport not found")
            return passport
        except Exception:
            logger.exception("Failed to get voter passport by ID", passport_id=passport_id)
            raise

    async def get_all_passports_by_voter_id(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> List[VoterPassport]:
        """Get all passport entries for a voter."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.voter_id == voter_id)
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get passports by voter ID", voter_id=voter_id)
            raise

    async def update_passport(
        self,
        session: AsyncSession,
        passport_id: UUID,
        dto: UpdateVoterPassportPlainDTO,
    ) -> VoterPassport:
        """Update a voter passport entry."""
        try:
            exclude = {"passport_id", "voter_id"}
            update_data = {
                k: v for k, v in asdict(dto).items()
                if k not in exclude and v is not None
            }

            if not update_data:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == passport_id)
                .values(**update_data)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()

            if not updated:
                raise NotFoundError("Voter passport not found")

            logger.info("Voter passport updated successfully", passport_id=passport_id)
            return updated

        except Exception:
            logger.exception("Failed to update voter passport", passport_id=passport_id)
            raise

    async def delete_passport(
        self,
        session: AsyncSession,
        passport_id: UUID,
        voter_id: UUID,
    ) -> None:
        """Delete a voter passport entry."""
        try:
            stmt = (
                delete(self._model)
                .where(self._model.id == passport_id)
                .where(self._model.voter_id == voter_id)
            )
            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise NotFoundError("Voter passport not found")

            logger.info("Voter passport deleted successfully", passport_id=passport_id)

        except Exception:
            logger.exception("Failed to delete voter passport", passport_id=passport_id, voter_id=voter_id)
            raise
