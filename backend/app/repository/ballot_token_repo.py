# ballot_token_repo.py - Repository layer for ballot token operations.

from typing import List, Type
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sqlalchemy.ballot_token import BallotToken

logger = structlog.get_logger()


class BallotTokenRepository:
    """Repository layer for ballot-token-related operations."""

    def __init__(self, model: Type[BallotToken] = BallotToken) -> None:
        self._model = model

    # ── Create ──

    async def create_bulk(
        self,
        session: AsyncSession,
        tokens: List[BallotToken],
    ) -> List[BallotToken]:
        """Persist a batch of new ballot tokens."""
        session.add_all(tokens)
        await session.flush()
        logger.info("Ballot tokens created", count=len(tokens))
        return tokens

    # ── Read ──

    async def get_by_blind_token_hash(
        self,
        session: AsyncSession,
        search_token: str,
    ) -> BallotToken | None:
        """Retrieve a ballot token by its blind_token_hash search token (HMAC blind index)."""
        result = await session.execute(
            select(self._model).where(
                self._model.blind_token_hash_search_token == search_token
            )
        )
        return result.scalar_one_or_none()

    async def get_by_election(
        self,
        session: AsyncSession,
        election_id: UUID,
        constituency_id: UUID | None = None,
    ) -> List[BallotToken]:
        """Get all ballot tokens for an election, optionally filtered by constituency."""
        stmt = select(self._model).where(self._model.election_id == election_id)
        if constituency_id is not None:
            stmt = stmt.where(self._model.constituency_id == constituency_id)
        stmt = stmt.order_by(self._model.issued_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_referendum(
        self,
        session: AsyncSession,
        referendum_id: UUID,
    ) -> List[BallotToken]:
        """Get all ballot tokens for a referendum."""
        stmt = (
            select(self._model)
            .where(self._model.referendum_id == referendum_id)
            .order_by(self._model.issued_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_election(
        self,
        session: AsyncSession,
        election_id: UUID,
        constituency_id: UUID | None = None,
    ) -> tuple[int, int]:
        """Return (total, used) counts for an election's tokens."""
        where = [self._model.election_id == election_id]
        if constituency_id is not None:
            where.append(self._model.constituency_id == constituency_id)

        total_q = select(func.count()).select_from(self._model).where(*where)
        used_q = select(func.count()).select_from(self._model).where(
            *where, self._model.is_used.is_(True)
        )
        total = (await session.execute(total_q)).scalar() or 0
        used = (await session.execute(used_q)).scalar() or 0
        return total, used

    async def count_by_referendum(
        self,
        session: AsyncSession,
        referendum_id: UUID,
    ) -> tuple[int, int]:
        """Return (total, used) counts for a referendum's tokens."""
        where = [self._model.referendum_id == referendum_id]

        total_q = select(func.count()).select_from(self._model).where(*where)
        used_q = select(func.count()).select_from(self._model).where(
            *where, self._model.is_used.is_(True)
        )
        total = (await session.execute(total_q)).scalar() or 0
        used = (await session.execute(used_q)).scalar() or 0
        return total, used

    # ── Update ──

    async def mark_as_used(
        self,
        session: AsyncSession,
        ballot_token_id: UUID,
        used_at,
    ) -> BallotToken:
        """Mark a ballot token as used."""
        stmt = (
            update(self._model)
            .where(self._model.id == ballot_token_id)
            .values(is_used=True, used_at=used_at)
            .returning(self._model)
        )
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise ValueError("Ballot token not found")

        logger.info("Ballot token marked as used", ballot_token_id=ballot_token_id)
        return token
