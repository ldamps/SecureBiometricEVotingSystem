# voter_service.py - Service layer for voter-related operations.

import structlog
from app.repository.voter_repo import VoterRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO, RegisterVoterEncryptedDTO
from app.models.schemas.voter import VoterItem
from uuid import UUID

logger = structlog.get_logger()

class VoterService:
    """Service layer for voter-related operations."""
    def __init__(
        self,
        voter_repo: VoterRepository,
        session: AsyncSession,
        voter: Optional[Voter] = None,
    ):
        """
        Service layer for voter-related operations.
        """
        self.voter_repo = voter_repo
        self.session = session
        self.voter = voter


    async def register_voter(
        self,
        dto: RegisterVoterPlainDTO
    ) -> VoterItem:
        """Create a new voter."""
        try:
            # Check if voter already exists

            # Register voter
            voter = await self.voter_repo.register_voter(
                self.session,
                dto,
            )

            # Return voter
            return voter
            
        except Exception:
            logger.exception(
                "Failed to register voter",
                dto=dto
            )
            raise
        
        
    async def _encrypt_dto_for_creation(
        self,
        dto: RegisterVoterEncryptedDTO
    ) -> RegisterVoterEncryptedDTO:
        """ Encrypt the DTO for creation. """
        pass


    async def get_voter_by_id(
        self,
        voter_id: UUID
    ) -> VoterItem:
        """ Get a voter by their ID. """
        try:
            voter = await self.voter_repo.get_voter_by_id(
                self.session,
                voter_id,
            )
            return voter
            
        except Exception:
            logger.exception(
                "Failed to get voter by ID",
                voter_id=voter_id
            )
            raise


    async def update_voter_details(
        self,
        dto: UpdateVoterPlainDTO
    ) -> VoterItem:
        """ Update a voter's details. """
        pass


    async def check_voter_exists(
        self,
        voter_id: UUID
    ) -> bool:
        """ Check if a voter exists. """
        pass

    async def check_voter_locked(
        self,
        voter_id: UUID
    ) -> bool:
        """ Check if a voter is locked. """
        pass

    async def check_voter_renewal_needed(
        self,
        voter_id: UUID
    ) -> bool:
        """ Check if a voter's account needs to be renewed. """
        pass

    async def get_user_addresses(
        self,
        voter_id: UUID
    ):
        """ Get a voter's addresses. """
        pass


    async def get_user_biometric_templates(
        self,
        voter_id: UUID
    ):
        """ Get a voter's biometric templates. """
        pass

    async def get_user_voter_ledger(
        self,
        voter_id: UUID
    ):
        """ Get a voter's voter ledger. """
        pass


