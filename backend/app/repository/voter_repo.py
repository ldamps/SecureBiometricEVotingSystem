# voter_repo.py - Repository layer for voter-related operations.

from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO
from app.application.core.exceptions import NotFoundError
from app.models.sqlalchemy.voter import Voter

logger = structlog.get_logger()

class VoterRepository:
    """Voter-specific repository operations."""

    def __init__(self):
        super().__init__(Voter)

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
                select(Voter.renew_by).where(
                    Voter.id == voter_id
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
                select(Voter).where(
                    Voter.email == email
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

    # CRUD METHODS ----------
    async def register_voter(self, 
        session: AsyncSession, 
        dto: RegisterVoterPlainDTO,
    ) -> Voter:
        """
        Register (create) a new voter.

        Args:
            session (AsyncSession): The database session.
            dto (VoterCreateDTO): The DTO containing voter details.

        Returns:
            Voter: The created voter.
        
        Raises:
            DatabaseError: If there is an error creating the voter.
        """
        try:
            voter = dto.to_model()
            session.add(voter)
            await session.flush()

            logger.info(
                "Voter created successfully",
                voter_id=voter.id
            )
            return voter

        except Exception:
            logger.exception(
                "Failed to create voter",
                dto=dto
            )
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
                select(Voter).where(
                    Voter.id == voter_id
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
                "passport_number",
                "passport_country",
                "consituency_id",
                "renew_by",
                "registration_status",
                "failed_auth_attempts",
                "locked_until",
                "registered_at",
                "renew_by",
            ]

            update_data = {
                field: getattr(dto, field)
                for field in allowed_fields
                if getattr(dto, field) is not None
            }

            if not update_data:
                raise ValueError("No valid fields to update")

            stmt = (
                update(Voter)
                .where(Voter.id == voter_id)
                .values(**update_data)
                .returning(Voter)
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


    # ------------------------------------------------------------
