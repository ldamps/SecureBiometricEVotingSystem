# voter_service.py - Service layer for voter-related operations.

import structlog
from app.repository.voter_repo import VoterRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import RegisterVoterPlainDTO
from app.models.schemas.voter import VoterItem

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
            pass

        except Exception:
            logger.exception(
                "Failed to register voter",
                voter_first_name=dto.first_name,
                voter_surname=dto.surname
            )
            raise


