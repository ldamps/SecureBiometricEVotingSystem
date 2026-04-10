# voter_repo.py - Repository layer for voter-related operations.

from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import UpdateVoterPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Optional, Type
from uuid import UUID
from datetime import datetime
from app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()

class VoterRepository:
    """Voter-specific repository operations."""

    def __init__(self, model: Type[Voter] = Voter) -> None:
        self._model = model

    # INTERNAL HELPER METHODS ----------
    
    async def check_voter_exists(
        self,
    ) -> bool:
        """
        Check if a voter exists.
        """
        try:
            pass
               
        except Exception:
            logger.exception(
                "Failed to check if voter exists"
            )
            raise

    async def check_voter_locked(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> Optional[datetime]:
        """
        Check if a voter's account is locked.
        """
        try:
            result = await session.execute(
                select(Voter.locked_until).where(
                    Voter.id == voter_id
                )
            )
            locked_until = result.scalar_one_or_none()
            if not locked_until:
                return None
            else:
                return locked_until

        except Exception:
            logger.exception(
                "Failed to check if voter is locked",
                voter_id=voter_id
            )
            raise

    async def check_voter_renewal_needed(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> Optional[datetime]:
        """
        Check if a voter's account needs to be renewed.
        """
        try:
            result = await session.execute(
                select(self._model.renew_by).where(
                    self._model.id == voter_id
                )
            )
            renew_by = result.scalar_one_or_none()
            return renew_by
            
        except Exception:
            logger.exception(
                "Failed to check if voter renewal is needed",
                voter_id=voter_id
            )
            raise

    async def check_voter_email_exists(
        self, 
        session: AsyncSession,
        email: str,
    ) -> bool:
        """
        Check if a voter with the given email already exists.
        """
        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.email == email
                )
            )
            voter = result.scalar_one_or_none()
            if not voter:
                return False
            else:
                return True

        except Exception:
            logger.exception(
                "Failed to check if voter email exists",
                email=email
            )
            raise

    # ------------------------------------------------------------

    async def update_constituency(
        self,
        session: AsyncSession,
        voter_id: UUID,
        constituency_id: UUID,
    ) -> None:
        """Set the voter's constituency_id."""
        try:
            stmt = (
                update(self._model)
                .where(self._model.id == voter_id)
                .values(constituency_id=constituency_id)
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise NotFoundError("Voter not found")
            logger.info("Voter constituency updated", voter_id=voter_id, constituency_id=constituency_id)
        except Exception:
            logger.exception("Failed to update voter constituency", voter_id=voter_id)
            raise

    async def get_voter_by_ni_search_token(
        self,
        session: AsyncSession,
        token: str,
    ) -> Optional[Voter]:
        """Look up a voter by their NI number search token (HMAC blind index)."""
        result = await session.execute(
            select(self._model).where(
                self._model.national_insurance_number_search_token == token
            )
        )
        return result.scalars().first()

    # CRUD METHODS ----------
    async def register_voter(self, session: AsyncSession, voter: Voter) -> Voter:
        """
        Persist a new voter (caller builds ORM row, e.g. with encrypted PII).
        """
        try:
            session.add(voter)
            await session.flush()

            logger.info(
                "Voter created successfully",
                voter_id=voter.id,
            )
            return voter

        except Exception:
            logger.exception("Failed to create voter")
            raise


    async def get_voter_by_id(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> Voter:
        """
        Get a voter and their details by their ID.

        Args:
            session (AsyncSession): The database session.
            voter_id (UUID): The ID of the voter.

        Returns:
            Voter: The voter and their details.
        
        Raises:
            NotFoundError: If the voter is not found.
        """

        try:
            result = await session.execute(
                select(self._model).where(
                    self._model.id == voter_id
                )
            )
            voter = result.scalar_one_or_none()
            if not voter:
                raise NotFoundError("Voter not found")
            return voter

        except Exception:
            logger.exception(
                "Failed to get voter by ID",
                voter_id=voter_id
            )
            raise


    async def update_voter_details(
        self,
        session: AsyncSession,
        voter_id: UUID,
        dto: UpdateVoterPlainDTO,
    ) -> Voter:
        """
        Update a voter's details by their voter ID.
        Can only update the following fields:
        - first name
        - surname
        - previous first name
        - previous surname
        - NI (only if the voter does not have an NI originally when they registered)
        - Passport number
        - Passport country
        - Consituency ID (if current address has changed)
        - Renew by date
        - Registration status
        - Failed authentication attempts
        - Locked until
        - Registered at
        - Renew by

        Args:
            session (AsyncSession): The database session.
            voter_id (UUID): The ID of the voter.
            dto (UpdateVoterPlainDTO): The DTO containing the voter details to update.

        Returns:
            Voter: The updated voter.
        
        Raises:
            NotFoundError: If the voter is not found.
        """
        try:
            allowed_fields = [
                "first_name",
                "surname",
                "previous_first_name",
                "previous_surname",
                "national_insurance_number",
                "nationality_category",
                "immigration_status",
                "immigration_status_expiry",
                "renew_by",
            ]

            # DTO uses constituency_id (typo); Voter model uses constituency_id
            column_map = {"constituency_id": "constituency_id"}
            update_data = {}
            for field in allowed_fields:
                val = getattr(dto, field, None)
                if val is not None:
                    update_data[column_map.get(field, field)] = val

            if not update_data:
                raise ValueError("No valid fields to update")

            stmt = (
                update(self._model)
                .where(self._model.id == voter_id)
                .values(**update_data)
                .returning(self._model)
            )

            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()

            if not updated:
                raise NotFoundError("Voter not found")

            logger.info(
                "Voter updated successfully",
                voter_id=voter_id
            )
            return updated

        except Exception:
            logger.exception(
                "Failed to update voter details",
                dto=dto
            )
            raise

    async def update_voter_status(
        self,
        session: AsyncSession,
        voter_id: UUID,
        voter_status: str,
        registration_status: str | None = None,
    ) -> Voter:
        """Update the voter's status (and optionally registration_status)."""
        try:
            values: dict = {"voter_status": voter_status}
            if registration_status is not None:
                values["registration_status"] = registration_status
            stmt = (
                update(self._model)
                .where(self._model.id == voter_id)
                .values(**values)
                .returning(self._model)
            )
            result = await session.execute(stmt)
            updated = result.scalar_one_or_none()
            if not updated:
                raise NotFoundError("Voter not found")
            logger.info("Voter status updated", voter_id=voter_id, voter_status=voter_status)
            return updated
        except NotFoundError:
            raise
        except Exception:
            logger.exception("Failed to update voter status", voter_id=voter_id)
            raise

    # ------------------------------------------------------------
