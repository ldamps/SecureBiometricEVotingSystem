# voter_ledger_repo.py - Repository layer for voter ledger-related operations.

from typing import Type, List
from app.models.sqlalchemy.voter_ledger import VoterLedger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.application.core.exceptions import NotFoundError
import structlog

logger = structlog.get_logger()

class VoterLedgerRepository:
    """Repository layer for voter ledger-related operations."""

    def __init__(self, model: Type[VoterLedger] = VoterLedger) -> None:
        self._model = model

    async def create_voter_ledger(
        self,
        session: AsyncSession,
        voter_ledger: VoterLedger,
    ) -> VoterLedger:
        """Create a new voter ledger entry."""
        try: 
            session.add(voter_ledger)
            await session.flush()

            logger.info(
                "Voter ledger created successfully",
                voter_id=voter_ledger.voter_id,
                election_id=voter_ledger.election_id,
            )

            return voter_ledger

        except Exception:
            logger.exception("Failed to create voter ledger")
            raise

    async def get_voter_ledger_by_id(
        self,
        session: AsyncSession,
        voter_ledger_id: UUID,
    ) -> VoterLedger:
        """Get a voter ledger entry by its ID."""
        try:
            result = await session.execute(
                select(self._model).
                where(self._model.id == voter_ledger_id)
            )
            voter_ledger = result.scalar_one_or_none()
            if not voter_ledger:
                raise NotFoundError("Voter ledger not found")
            return voter_ledger
        except Exception:
            logger.exception("Failed to get voter ledger by ID", voter_ledger_id=voter_ledger_id)
            raise

    async def get_all_voter_ledger_entries_by_voter_id(
        self,
        session: AsyncSession,
        voter_id: UUID,
    ) -> List[VoterLedger]:
        """Get all voter ledger entries for a voter."""
        try:
            result = await session.execute(
                select(self._model).where(self._model.voter_id == voter_id)
            )   
            return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to get all voter ledger entries by voter ID", voter_id=voter_id)
            raise
