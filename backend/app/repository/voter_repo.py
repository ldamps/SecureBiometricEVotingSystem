from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
from typing import Optional
from uuid import UUID

from backend.app.models.dto import voter
from backend.app.application.core.exceptions import NotFoundError

logger = structlog.get_logger()

class VoterRepository:
    """Voter-specific repository operations."""

    def __init__(self):
        super().__init__()

    # INTERNAL HELPER METHODS ----------
    
    async def check_voter_exists(
        self,
        first_name: str,
        surname: str,
        email: str,
        national_insurance_number: Optional[str] = None,
        passport_number: Optional[str] = None,
        passport_country: Optional[str] = None,
    ) -> bool:
        """
        Check if a voter exists using the email, first name, surname and optionally national insurance number or passport number + country.
        """
        try:
            pass
               
            
            
        except Exception:
            logger.exception(
                "Failed to check if voter exists"
            )
            raise

    # is account locked? has too many failed auth attempts?


    # renewal needed?


    # does registration with this email already exist?
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

        pass


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
                    Voter.voter_id == voter_id
                )
            )
            voter = result.scalar_one_or_none()
            if not voter:
                raise NotFoundError("Voter not found")

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

        Args:
            session (AsyncSession): The database session.
            voter_id (UUID): The ID of the voter.
            dto (UpdateVoterPlainDTO): The DTO containing the voter details to update.

        Returns:
            Voter: The updated voter.
        
        Raises:
            NotFoundError: If the voter is not found.
        """
        pass



    # ------------------------------------------------------------
