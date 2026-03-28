# voting_service.py - Service layer for casting votes (elections and referendums).

import secrets
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from app.models.dto.vote import CreateVotePlainDTO, CreateVoteEncryptedDTO
from app.models.dto.referendum_vote import CreateReferendumVoteEncryptedDTO
from app.models.schemas.vote import (
    CastVoteRequest,
    CastVoteResponse,
    CastReferendumVoteRequest,
    CastReferendumVoteResponse,
)
from app.models.sqlalchemy.election import Election, ElectionStatus
from app.models.sqlalchemy.voter_ledger import VoterLedger
from app.repository.ballot_token_repo import BallotTokenRepository
from app.repository.tally_result_repo import TallyResultRepository
from app.repository.candidate_repo import CandidateRepository
from app.repository.voter_repo import VoterRepository
from app.repository.vote_repo import VoteRepository
from app.repository.referendum_vote_repo import ReferendumVoteRepository
from app.repository.voter_ledger_repo import VoterLedgerRepository
from app.repository.election_repo import ElectionRepository
from app.repository.referendum_repo import ReferendumRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.keys_manager_service import KeysManagerService

logger = structlog.get_logger()


class VotingService(EncryptionUtilsMixin):
    """Service layer for casting votes.

    Ensures:
    - Each voter can vote exactly once per election (checked via Voter_Ledger).
    - Votes are anonymous (the Vote record has NO voter_id).
    - The blind ballot token is validated and marked as used.
    - A Voter_Ledger entry is created to record participation.
    - The tally is incremented for the chosen candidate.
    - An optional email confirmation can be sent.
    """

    def __init__(
        self,
        vote_repo: VoteRepository,
        referendum_vote_repo: ReferendumVoteRepository,
        ballot_token_repo: BallotTokenRepository,
        voter_ledger_repo: VoterLedgerRepository,
        tally_result_repo: TallyResultRepository,
        election_repo: ElectionRepository,
        referendum_repo: ReferendumRepository,
        candidate_repo: CandidateRepository,
        voter_repo: VoterRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.vote_repo = vote_repo
        self.referendum_vote_repo = referendum_vote_repo
        self.ballot_token_repo = ballot_token_repo
        self.voter_ledger_repo = voter_ledger_repo
        self.tally_result_repo = tally_result_repo
        self.election_repo = election_repo
        self.referendum_repo = referendum_repo
        self.candidate_repo = candidate_repo
        self.voter_repo = voter_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def cast_vote(self, request: CastVoteRequest) -> CastVoteResponse:
        """Cast a vote in an election.

        Flow:
        1. Validate the election exists and is OPEN.
        2. Check Voter_Ledger — reject if voter already voted in this election.
        3. Validate the blind ballot token (exists, unused, matches election).
        4. Create the anonymous Vote record (no voter_id).
        5. Mark the ballot token as used.
        6. Create a Voter_Ledger entry (voter_id + election_id).
        7. Increment the tally for the chosen candidate.
        8. Optionally queue an email confirmation.
        9. Return a receipt code.
        """
        voter_id = UUID(request.voter_id)
        election_id = UUID(request.election_id)
        constituency_id = UUID(request.constituency_id)
        candidate_id = UUID(request.candidate_id)
        blind_token_hash = request.blind_token_hash
        now = datetime.now(timezone.utc)

        # 1. Validate the election exists and is OPEN
        election = await self.election_repo.get_election_by_id(self.session, election_id)
        if election.status != ElectionStatus.OPEN.value:
            raise ValidationError("Election is not open for voting.")

        # 1b. Validate the voter exists
        await self.voter_repo.get_voter_by_id(self.session, voter_id)

        # 2. Check Voter_Ledger — has this voter already voted?
        existing_ledger = await self._get_voter_ledger_entry(voter_id, election_id)
        if existing_ledger:
            raise ValidationError(
                "You have already voted in this election. Each voter may only vote once."
            )

        # 3. Validate the blind ballot token (lookup via HMAC search token)
        search_token = await self._compute_ballot_search_token(blind_token_hash)
        ballot_token = await self.ballot_token_repo.get_by_blind_token_hash(
            self.session, search_token
        )
        if not ballot_token:
            raise ValidationError("Invalid ballot token.")
        if ballot_token.is_used:
            raise ValidationError("This ballot token has already been used.")
        if ballot_token.election_id != election_id:
            raise ValidationError("Ballot token does not belong to this election.")
        if ballot_token.constituency_id != constituency_id:
            raise ValidationError("Ballot token does not belong to this constituency.")

        # 3b. Validate the candidate exists
        await self.candidate_repo.get_candidate_by_id(self.session, candidate_id)

        # 4. Create the anonymous vote record (NO voter_id — preserves anonymity)
        receipt_code = secrets.token_urlsafe(32)

        vote_dto = CreateVotePlainDTO(
            election_id=election_id,
            constituency_id=constituency_id,
            candidate_id=candidate_id,
            blind_token_hash=str(blind_token_hash),
            receipt_code=receipt_code,
            email_sent=request.send_email_confirmation,
            cast_at=now,
        )

        vote_enc_dto = CreateVoteEncryptedDTO(
            election_id=vote_dto.election_id,
            constituency_id=vote_dto.constituency_id,
            candidate_id=vote_dto.candidate_id,
            blind_token_hash=vote_dto.blind_token_hash,
            receipt_code=vote_dto.receipt_code,
            email_sent=vote_dto.email_sent,
            cast_at=vote_dto.cast_at,
        )
        vote_model = vote_enc_dto.to_model()
        vote = await self.vote_repo.create_vote(self.session, vote_model)

        # 5. Mark the ballot token as used
        await self.ballot_token_repo.mark_as_used(
            self.session, ballot_token.id, used_at=now
        )

        # 6. Create a Voter_Ledger entry (records participation, NOT the vote choice)
        await self._create_voter_ledger_entry(voter_id, election_id, now)

        # 7. Increment the tally for the chosen candidate
        await self.tally_result_repo.increment_vote_count(
            self.session,
            election_id=election_id,
            constituency_id=constituency_id,
            candidate_id=candidate_id,
        )

        # 8. Optionally send email confirmation (non-blocking)
        if request.send_email_confirmation:
            try:
                await self._send_vote_confirmation_email(voter_id, election.title)
            except Exception:
                logger.warning(
                    "Failed to send vote confirmation email",
                    voter_id=str(voter_id),
                    election_id=str(election_id),
                )

        logger.info(
            "Vote cast successfully",
            election_id=str(election_id),
            constituency_id=str(constituency_id),
        )

        # 9. Return receipt
        return CastVoteResponse(
            id=str(vote.id),
            receipt_code=receipt_code,
            election_id=str(election_id),
            constituency_id=str(constituency_id),
            cast_at=now,
            message="Your vote has been cast successfully. You cannot change your vote.",
        )

    async def cast_referendum_vote(
        self, request: CastReferendumVoteRequest
    ) -> CastReferendumVoteResponse:
        """Cast a vote on a referendum (YES or NO).

        Flow:
        1. Validate the referendum exists and is OPEN.
        2. Check Voter_Ledger — reject if voter already voted in this referendum.
        3. Validate the blind ballot token (exists, unused, matches referendum).
        4. Create the anonymous ReferendumVote record (no voter_id).
        5. Mark the ballot token as used.
        6. Create a Voter_Ledger entry (voter_id + referendum_id).
        7. Increment the referendum tally for the chosen answer.
        8. Optionally queue an email confirmation.
        9. Return a receipt code.
        """
        voter_id = UUID(request.voter_id)
        referendum_id = UUID(request.referendum_id)
        choice = request.choice.upper()
        blind_token_hash = request.blind_token_hash
        now = datetime.now(timezone.utc)

        # 1. Validate the referendum exists and is OPEN
        referendum = await self.referendum_repo.get_referendum_by_id(
            self.session, referendum_id
        )
        if referendum.status != "OPEN":
            raise ValidationError("Referendum is not open for voting.")

        # 1b. Validate the voter exists
        await self.voter_repo.get_voter_by_id(self.session, voter_id)

        # 2. Check Voter_Ledger — has this voter already voted?
        existing_ledger = await self._get_referendum_voter_ledger_entry(
            voter_id, referendum_id
        )
        if existing_ledger:
            raise ValidationError(
                "You have already voted in this referendum. Each voter may only vote once."
            )

        # 3. Validate the blind ballot token (lookup via HMAC search token)
        search_token = await self._compute_ballot_search_token(blind_token_hash)
        ballot_token = await self.ballot_token_repo.get_by_blind_token_hash(
            self.session, search_token
        )
        if not ballot_token:
            raise ValidationError("Invalid ballot token.")
        if ballot_token.is_used:
            raise ValidationError("This ballot token has already been used.")
        if ballot_token.referendum_id != referendum_id:
            raise ValidationError("Ballot token does not belong to this referendum.")

        # 4. Create the anonymous referendum vote record (NO voter_id)
        receipt_code = secrets.token_urlsafe(32)

        vote_enc_dto = CreateReferendumVoteEncryptedDTO(
            referendum_id=referendum_id,
            choice=choice,
            blind_token_hash=str(blind_token_hash),
            receipt_code=receipt_code,
            email_sent=request.send_email_confirmation,
            cast_at=now,
        )
        vote_model = vote_enc_dto.to_model()
        vote = await self.referendum_vote_repo.create_vote(self.session, vote_model)

        # 5. Mark the ballot token as used
        await self.ballot_token_repo.mark_as_used(
            self.session, ballot_token.id, used_at=now
        )

        # 6. Create a Voter_Ledger entry (records participation, NOT the vote choice)
        await self._create_referendum_voter_ledger_entry(voter_id, referendum_id, now)

        # 7. Increment the referendum tally
        await self.tally_result_repo.increment_referendum_vote_count(
            self.session,
            referendum_id=referendum_id,
            choice=choice,
        )

        # 8. Optionally send email confirmation (non-blocking)
        if request.send_email_confirmation:
            try:
                await self._send_vote_confirmation_email(voter_id, referendum.title)
            except Exception:
                logger.warning(
                    "Failed to send referendum vote confirmation email",
                    voter_id=str(voter_id),
                    referendum_id=str(referendum_id),
                )

        logger.info(
            "Referendum vote cast successfully",
            referendum_id=str(referendum_id),
            choice=choice,
        )

        # 9. Return receipt
        return CastReferendumVoteResponse(
            id=str(vote.id),
            receipt_code=receipt_code,
            referendum_id=str(referendum_id),
            cast_at=now,
            message="Your referendum vote has been cast successfully. You cannot change your vote.",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_voter_ledger_entry(
        self, voter_id: UUID, election_id: UUID
    ) -> VoterLedger | None:
        """Check if the voter already has a ledger entry for this election."""
        result = await self.session.execute(
            select(VoterLedger).where(
                VoterLedger.voter_id == voter_id,
                VoterLedger.election_id == election_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_referendum_voter_ledger_entry(
        self, voter_id: UUID, referendum_id: UUID
    ) -> VoterLedger | None:
        """Check if the voter already has a ledger entry for this referendum."""
        result = await self.session.execute(
            select(VoterLedger).where(
                VoterLedger.voter_id == voter_id,
                VoterLedger.referendum_id == referendum_id,
            )
        )
        return result.scalar_one_or_none()

    async def _create_voter_ledger_entry(
        self, voter_id: UUID, election_id: UUID, voted_at: datetime
    ) -> VoterLedger:
        """Create a voter ledger entry recording election participation."""
        ledger = VoterLedger(
            voter_id=voter_id,
            election_id=election_id,
            voted_at=voted_at,
        )
        self.session.add(ledger)
        await self.session.flush()
        logger.info(
            "Voter ledger entry created",
            voter_id=str(voter_id),
            election_id=str(election_id),
        )
        return ledger

    async def _create_referendum_voter_ledger_entry(
        self, voter_id: UUID, referendum_id: UUID, voted_at: datetime
    ) -> VoterLedger:
        """Create a voter ledger entry recording referendum participation."""
        ledger = VoterLedger(
            voter_id=voter_id,
            referendum_id=referendum_id,
            voted_at=voted_at,
        )
        self.session.add(ledger)
        await self.session.flush()
        logger.info(
            "Voter ledger entry created",
            voter_id=str(voter_id),
            referendum_id=str(referendum_id),
        )
        return ledger

    async def _compute_ballot_search_token(self, blind_token_hash: str) -> str:
        """Compute the HMAC search token for a plaintext blind_token_hash."""
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)
        return await self._mapper.create_search_token(blind_token_hash, args, self.session)

    async def _send_vote_confirmation_email(
        self, voter_id: UUID, election_name: str
    ) -> None:
        """Send a vote confirmation email to the voter.

        Note: The email service infrastructure (SMTP client) is not yet
        implemented. This method is a placeholder that logs the intent.
        Once the email infra is wired up, replace with actual send logic.
        """
        logger.info(
            "Vote confirmation email queued",
            voter_id=str(voter_id),
            election_name=election_name,
            template="voting_confirmation.html",
        )
