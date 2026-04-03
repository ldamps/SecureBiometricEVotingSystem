# ballot_service.py - Service layer for ballot token issuance and management.

import uuid
from datetime import datetime, timezone
from typing import List
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import NotFoundError, ValidationError
from app.models.dto.ballot import (
    BallotTokenBaseDTO,
    BallotTokenDTO,
    CreateBallotTokenEncryptedDTO,
    CreateBallotTokenPlainDTO,
)
from app.models.schemas.ballot_token import (
    BallotTokenItem,
    BallotTokenStatusResponse,
    IssueBallotTokenRequest,
    IssueBallotTokenResponse,
    IssueReferendumBallotTokenRequest,
    IssueReferendumBallotTokenResponse,
)
from app.models.sqlalchemy.ballot_token import BallotToken
from app.models.sqlalchemy.election import Election, ElectionStatus
from app.models.sqlalchemy.referendum import ReferendumStatus
from app.repository.ballot_token_repo import BallotTokenRepository
from app.repository.election_repo import ElectionRepository
from app.repository.referendum_repo import ReferendumRepository
from app.service.base.encryption_utils_mixin import (
    EncryptionUtilsMixin,
)
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


def _ballot_token_orm_to_dto_unencrypted_row(token: BallotToken) -> BallotTokenDTO:
    """Map ballot token ORM row when columns hold plaintext (legacy/migration)."""
    raw = getattr(token, "blind_token_hash", None)
    if raw is None:
        bth = None
    elif isinstance(raw, str):
        bth = raw
    elif isinstance(raw, uuid.UUID):
        bth = str(raw)
    else:
        bth = None

    return BallotTokenDTO(
        id=token.id,
        election_id=token.election_id,
        constituency_id=token.constituency_id,
        referendum_id=token.referendum_id,
        blind_token_hash=bth,
        is_used=token.is_used,
        issued_at=token.issued_at,
        used_at=token.used_at,
    )


class BallotTokenService(EncryptionUtilsMixin):
    """Service layer for issuing and querying ballot tokens.

    Tokens are one-time-use: once consumed via the voting endpoint the token
    cannot be reused. The ``blind_token_hash`` is encrypted at rest with a
    companion HMAC search token for lookups.
    """

    def __init__(
        self,
        ballot_token_repo: BallotTokenRepository,
        election_repo: ElectionRepository,
        referendum_repo: ReferendumRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.ballot_token_repo = ballot_token_repo
        self.election_repo = election_repo
        self.referendum_repo = referendum_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    # ------------------------------------------------------------------ #
    #  Issue tokens                                                        #
    # ------------------------------------------------------------------ #

    async def issue_election_tokens(
        self, request: IssueBallotTokenRequest
    ) -> IssueBallotTokenResponse:
        """Generate *count* ballot tokens for an election + constituency."""
        election_id = UUID(request.election_id)
        constituency_id = UUID(request.constituency_id)
        count = request.count

        # Validate election exists
        election = await self.election_repo.get_election_by_id(self.session, election_id)
        if election.status != ElectionStatus.OPEN.value:
            raise ValidationError(
                "Ballot tokens can only be issued while the election status is OPEN."
            )

        now = datetime.now(timezone.utc)

        # Init encryption keys
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

        models: list[BallotToken] = []
        plain_hashes: list[str] = []

        for _ in range(count):
            token_value = str(uuid.uuid4())
            plain_hashes.append(token_value)

            plain_dto = CreateBallotTokenPlainDTO(
                election_id=election_id,
                constituency_id=constituency_id,
                blind_token_hash=token_value,
                issued_at=now,
            )

            enc_dto = await self._mapper.encrypt_dto(
                plain_dto, CreateBallotTokenEncryptedDTO, args, self.session
            )
            models.append(enc_dto.to_model())

        await self.ballot_token_repo.create_bulk(self.session, models)

        logger.info(
            "Election ballot tokens issued",
            election_id=str(election_id),
            constituency_id=str(constituency_id),
            count=count,
        )

        return IssueBallotTokenResponse(
            election_id=str(election_id),
            constituency_id=str(constituency_id),
            tokens_issued=count,
            blind_token_hashes=plain_hashes,
        )

    async def issue_referendum_tokens(
        self, request: IssueReferendumBallotTokenRequest
    ) -> IssueReferendumBallotTokenResponse:
        """Generate *count* ballot tokens for a referendum."""
        referendum_id = UUID(request.referendum_id)
        count = request.count

        # Validate referendum exists
        referendum = await self.referendum_repo.get_referendum_by_id(
            self.session, referendum_id
        )
        if referendum.status != ReferendumStatus.OPEN.value:
            raise ValidationError(
                "Ballot tokens can only be issued while the referendum status is OPEN."
            )

        now = datetime.now(timezone.utc)

        # Init encryption keys
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

        models: list[BallotToken] = []
        plain_hashes: list[str] = []

        for _ in range(count):
            token_value = str(uuid.uuid4())
            plain_hashes.append(token_value)

            plain_dto = CreateBallotTokenPlainDTO(
                referendum_id=referendum_id,
                blind_token_hash=token_value,
                issued_at=now,
            )

            enc_dto = await self._mapper.encrypt_dto(
                plain_dto, CreateBallotTokenEncryptedDTO, args, self.session
            )
            models.append(enc_dto.to_model())

        await self.ballot_token_repo.create_bulk(self.session, models)

        logger.info(
            "Referendum ballot tokens issued",
            referendum_id=str(referendum_id),
            count=count,
        )

        return IssueReferendumBallotTokenResponse(
            referendum_id=str(referendum_id),
            tokens_issued=count,
            blind_token_hashes=plain_hashes,
        )

    # ------------------------------------------------------------------ #
    #  Voter-facing: issue a single token for the voter                    #
    # ------------------------------------------------------------------ #

    async def issue_voter_election_token(
        self, election_id: UUID, constituency_id: UUID,
    ) -> str:
        """Issue a single ballot token for a voter casting an election vote.

        Returns the plain token hash the voter must include in their cast-vote request.
        """
        election = await self.election_repo.get_election_by_id(self.session, election_id)
        if election.status != ElectionStatus.OPEN.value:
            raise ValidationError("Election is not open for voting.")

        now = datetime.now(timezone.utc)
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

        token_value = str(uuid.uuid4())
        plain_dto = CreateBallotTokenPlainDTO(
            election_id=election_id,
            constituency_id=constituency_id,
            blind_token_hash=token_value,
            issued_at=now,
        )
        enc_dto = await self._mapper.encrypt_dto(
            plain_dto, CreateBallotTokenEncryptedDTO, args, self.session
        )
        await self.ballot_token_repo.create_bulk(self.session, [enc_dto.to_model()])
        return token_value

    async def issue_voter_referendum_token(
        self, referendum_id: UUID,
    ) -> str:
        """Issue a single ballot token for a voter casting a referendum vote.

        Returns the plain token hash the voter must include in their cast-vote request.
        """
        referendum = await self.referendum_repo.get_referendum_by_id(
            self.session, referendum_id
        )
        if referendum.status != ReferendumStatus.OPEN.value:
            raise ValidationError("Referendum is not open for voting.")

        now = datetime.now(timezone.utc)
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

        token_value = str(uuid.uuid4())
        plain_dto = CreateBallotTokenPlainDTO(
            referendum_id=referendum_id,
            blind_token_hash=token_value,
            issued_at=now,
        )
        enc_dto = await self._mapper.encrypt_dto(
            plain_dto, CreateBallotTokenEncryptedDTO, args, self.session
        )
        await self.ballot_token_repo.create_bulk(self.session, [enc_dto.to_model()])
        return token_value

    # ------------------------------------------------------------------ #
    #  Query tokens                                                        #
    # ------------------------------------------------------------------ #

    async def get_election_token_status(
        self,
        election_id: UUID,
        constituency_id: UUID | None = None,
    ) -> BallotTokenStatusResponse:
        """Return usage summary for an election's ballot tokens."""
        await self.election_repo.get_election_by_id(self.session, election_id)
        total, used = await self.ballot_token_repo.count_by_election(
            self.session, election_id, constituency_id
        )
        return BallotTokenStatusResponse(total=total, used=used, unused=total - used)

    async def get_referendum_token_status(
        self,
        referendum_id: UUID,
    ) -> BallotTokenStatusResponse:
        """Return usage summary for a referendum's ballot tokens."""
        await self.referendum_repo.get_referendum_by_id(self.session, referendum_id)
        total, used = await self.ballot_token_repo.count_by_referendum(
            self.session, referendum_id
        )
        return BallotTokenStatusResponse(total=total, used=used, unused=total - used)

    async def get_election_tokens(
        self,
        election_id: UUID,
        constituency_id: UUID | None = None,
    ) -> List[BallotTokenItem]:
        """List all ballot tokens for an election (with decrypted hashes)."""
        await self.election_repo.get_election_by_id(self.session, election_id)
        tokens = await self.ballot_token_repo.get_by_election(
            self.session, election_id, constituency_id
        )
        return [
            await self.ballot_token_model_to_schema_item(t, self.session)
            for t in tokens
        ]

    async def get_referendum_tokens(
        self,
        referendum_id: UUID,
    ) -> List[BallotTokenItem]:
        """List all ballot tokens for a referendum (with decrypted hashes)."""
        await self.referendum_repo.get_referendum_by_id(self.session, referendum_id)
        tokens = await self.ballot_token_repo.get_by_referendum(
            self.session, referendum_id
        )
        return [
            await self.ballot_token_model_to_schema_item(t, self.session)
            for t in tokens
        ]

    # ------------------------------------------------------------------ #
    #  ORM → schema helper                                                 #
    # ------------------------------------------------------------------ #

    async def ballot_token_model_to_schema_item(
        self, token: BallotToken, session
    ) -> BallotTokenItem:
        """Decrypt and map a BallotToken ORM model to an API schema."""
        return await self._orm_to_schema_item(
            token,
            plain_dto_class=BallotTokenDTO,
            base_dto_class=BallotTokenBaseDTO,
            session=session,
            map_unencrypted_row=_ballot_token_orm_to_dto_unencrypted_row,
        )
