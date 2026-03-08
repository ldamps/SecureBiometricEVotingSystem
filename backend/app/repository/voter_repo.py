from app.models.sqlalchemy.voter import Voter
from app.models.dto.voter import RegisterVoterPlainDTO
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()

class VoterRepository:
    """Voter-specific repository operations."""

    def __init__(self):
        super().__init__()

    # INTERNAL HELPER METHODS ----------


    # CRUD METHODS ----------
    async def create_voter(self, session: AsyncSession, dto: RegisterVoterPlainDTO) -> Voter:
        """
        Register a new voter.

        Args:
            session (AsyncSession): The database session.
            dto (VoterCreateDTO): The DTO containing voter details.

        Returns:
            Voter: The created voter.
        
        Raises:
            DatabaseError: If there is an error creating the voter.
        """
        try:
            # does this voter already exist?

            
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
                voter_first_name=dto.first_name,
                voter_surname=dto.surname
            )
            raise
