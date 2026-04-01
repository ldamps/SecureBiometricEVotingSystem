# voting_service.py - Service layer for casting votes (elections and referendums).

import secrets
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from app.models.dto.vote import CreateVotePlainDTO, CreateVoteEncryptedDTO
from app.models.sqlalchemy.election import AllocationMethod, ELECTION_TYPE_ALLOCATION_MAP, ElectionType
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
from app.service.email_service import EmailService
from app.repository.audit_log_repo import AuditLogRepository
from app.models.sqlalchemy.audit_log import AuditLog

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
        email_service: EmailService | None = None,
        audit_log_repo: AuditLogRepository | None = None,
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
        self._email_service = email_service
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

    async def cast_vote(self, request: CastVoteRequest) -> CastVoteResponse:
        """Cast a vote in an election.

        Supports UK electoral systems:
        - FPTP: single candidate_id per constituency.
        - AMS: constituency candidate_id AND/OR regional party_id.
        - STV / AV: ranked_preferences list of (candidate_id, preference_rank).

        Flow:
        1. Validate the election exists and is OPEN; derive allocation method.
        2. Validate the ballot payload against the allocation method.
        3. Check Voter_Ledger — reject if voter already voted.
        4. Validate the blind ballot token.
        5. Create anonymous Vote record(s).
        6. Mark the ballot token as used.
        7. Create a Voter_Ledger entry.
        8. Increment tallies.
        9. Optionally queue an email confirmation.
        10. Return a receipt code.
        """
        voter_id = UUID(request.voter_id)
        election_id = UUID(request.election_id)
        constituency_id = UUID(request.constituency_id) if request.constituency_id else None
        candidate_id = UUID(request.candidate_id) if request.candidate_id else None
        party_id = UUID(request.party_id) if request.party_id else None
        blind_token_hash = request.blind_token_hash
        now = datetime.now(timezone.utc)

        # 1. Validate the election exists and is OPEN
        election = await self.election_repo.get_election_by_id(self.session, election_id)
        if election.status != ElectionStatus.OPEN.value:
            raise ValidationError("Election is not open for voting.")

        allocation_method = election.allocation_method

        # 1b. Validate the voter exists
        await self.voter_repo.get_voter_by_id(self.session, voter_id)

        # 2. Validate ballot payload against the allocation method
        self._validate_ballot_payload(allocation_method, request)

        # 3. Check Voter_Ledger — has this voter already voted?
        existing_ledger = await self._get_voter_ledger_entry(voter_id, election_id)
        if existing_ledger:
            raise ValidationError(
                "You have already voted in this election. Each voter may only vote once."
            )

        # 4. Validate the blind ballot token (lookup via HMAC search token)
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
        if constituency_id and ballot_token.constituency_id != constituency_id:
            raise ValidationError("Ballot token does not belong to this constituency.")

        # 4b. Validate candidate/party exist
        if candidate_id:
            await self.candidate_repo.get_candidate_by_id(self.session, candidate_id)

        # 5. Create anonymous vote record(s)
        receipt_code = secrets.token_urlsafe(32)
        vote = None

        if allocation_method in (
            AllocationMethod.STV.value,
            AllocationMethod.ALTERNATIVE_VOTE.value,
        ):
            # Ranked ballot: one Vote row per preference
            for pref in request.ranked_preferences:
                pref_candidate_id = UUID(pref.candidate_id)
                await self.candidate_repo.get_candidate_by_id(self.session, pref_candidate_id)
                vote_enc_dto = CreateVoteEncryptedDTO(
                    election_id=election_id,
                    constituency_id=constituency_id,
                    candidate_id=pref_candidate_id,
                    preference_rank=pref.preference_rank,
                    blind_token_hash=f"{blind_token_hash}:rank{pref.preference_rank}",
                    receipt_code=f"{receipt_code}:rank{pref.preference_rank}" if pref.preference_rank > 1 else receipt_code,
                    email_sent=request.send_email_confirmation if pref.preference_rank == 1 else False,
                    cast_at=now,
                )
                vote_model = vote_enc_dto.to_model()
                v = await self.vote_repo.create_vote(self.session, vote_model)
                if pref.preference_rank == 1:
                    vote = v
        elif allocation_method == AllocationMethod.AMS.value:
            # AMS: up to two vote rows — constituency (candidate) + regional (party)
            if candidate_id:
                vote_enc_dto = CreateVoteEncryptedDTO(
                    election_id=election_id,
                    constituency_id=constituency_id,
                    candidate_id=candidate_id,
                    blind_token_hash=str(blind_token_hash),
                    receipt_code=receipt_code,
                    email_sent=request.send_email_confirmation,
                    cast_at=now,
                )
                vote_model = vote_enc_dto.to_model()
                vote = await self.vote_repo.create_vote(self.session, vote_model)
            if party_id:
                list_vote_enc_dto = CreateVoteEncryptedDTO(
                    election_id=election_id,
                    constituency_id=constituency_id,
                    party_id=party_id,
                    blind_token_hash=f"{blind_token_hash}:list" if candidate_id else str(blind_token_hash),
                    receipt_code=f"{receipt_code}:list" if candidate_id else receipt_code,
                    email_sent=False,
                    cast_at=now,
                )
                list_vote_model = list_vote_enc_dto.to_model()
                list_vote = await self.vote_repo.create_vote(self.session, list_vote_model)
                if not vote:
                    vote = list_vote
        else:
            # FPTP: single candidate per constituency
            vote_enc_dto = CreateVoteEncryptedDTO(
                election_id=election_id,
                constituency_id=constituency_id,
                candidate_id=candidate_id,
                blind_token_hash=str(blind_token_hash),
                receipt_code=receipt_code,
                email_sent=request.send_email_confirmation,
                cast_at=now,
            )
            vote_model = vote_enc_dto.to_model()
            vote = await self.vote_repo.create_vote(self.session, vote_model)

        # 6. Mark the ballot token as used
        await self.ballot_token_repo.mark_as_used(
            self.session, ballot_token.id, used_at=now
        )

        # 7. Create a Voter_Ledger entry (records participation, NOT the vote choice)
        await self._create_voter_ledger_entry(voter_id, election_id, now)

        # 8. Increment tallies
        if allocation_method in (
            AllocationMethod.STV.value,
            AllocationMethod.ALTERNATIVE_VOTE.value,
        ):
            # For STV/AV only first-preference counts go into the tally initially;
            # subsequent rounds are computed at result time.
            first_pref = request.ranked_preferences[0]
            await self.tally_result_repo.increment_vote_count(
                self.session,
                election_id=election_id,
                constituency_id=constituency_id,
                candidate_id=UUID(first_pref.candidate_id),
            )
        elif allocation_method == AllocationMethod.AMS.value:
            if candidate_id:
                await self.tally_result_repo.increment_vote_count(
                    self.session,
                    election_id=election_id,
                    constituency_id=constituency_id,
                    candidate_id=candidate_id,
                )
        else:
            await self.tally_result_repo.increment_vote_count(
                self.session,
                election_id=election_id,
                constituency_id=constituency_id,
                candidate_id=candidate_id,
            )

        # 9. Optionally send email confirmation (non-blocking)
        if request.send_email_confirmation:
            try:
                await self._send_vote_confirmation_email(voter_id, election.title, "election")
            except Exception:
                logger.warning(
                    "Failed to send vote confirmation email",
                    voter_id=str(voter_id),
                    election_id=str(election_id),
                )

        # 9b. Audit: vote cast (no voter_id to preserve anonymity)
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="VOTE_CAST",
                action="CREATE",
                summary=f"Vote cast in election {election_id}",
                resource_type="vote",
                resource_id=vote.id,
                election_id=election_id,
                actor_type="VOTER",
            ),
        )

        logger.info(
            "Vote cast successfully",
            election_id=str(election_id),
            constituency_id=str(constituency_id) if constituency_id else "N/A",
        )

        # 10. Return receipt
        return CastVoteResponse(
            id=str(vote.id),
            receipt_code=receipt_code,
            election_id=str(election_id),
            constituency_id=str(constituency_id) if constituency_id else None,
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
                await self._send_vote_confirmation_email(voter_id, referendum.title, "referendum")
            except Exception:
                logger.warning(
                    "Failed to send referendum vote confirmation email",
                    voter_id=str(voter_id),
                    referendum_id=str(referendum_id),
                )

        # 8b. Audit: referendum vote cast (no voter_id to preserve anonymity)
        await self._audit_log_repo.create_audit_log(
            self.session,
            AuditLog(
                event_type="VOTE_CAST",
                action="CREATE",
                summary=f"Referendum vote cast in referendum {referendum_id}",
                resource_type="referendum_vote",
                resource_id=vote.id,
                actor_type="VOTER",
            ),
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

    @staticmethod
    def _validate_ballot_payload(
        allocation_method: str, request: CastVoteRequest
    ) -> None:
        """Ensure the request fields match the election's electoral system."""
        if allocation_method == AllocationMethod.FPTP.value:
            if not request.candidate_id:
                raise ValidationError("FPTP elections require a candidate_id.")
            if not request.constituency_id:
                raise ValidationError("FPTP elections require a constituency_id.")
        elif allocation_method == AllocationMethod.AMS.value:
            if not request.candidate_id and not request.party_id:
                raise ValidationError(
                    "AMS elections require a candidate_id (constituency vote) "
                    "and/or a party_id (regional list vote)."
                )
        elif allocation_method in (
            AllocationMethod.STV.value,
            AllocationMethod.ALTERNATIVE_VOTE.value,
        ):
            if not request.ranked_preferences:
                raise ValidationError(
                    f"{allocation_method} elections require ranked_preferences."
                )
            ranks = [p.preference_rank for p in request.ranked_preferences]
            if sorted(ranks) != list(range(1, len(ranks) + 1)):
                raise ValidationError(
                    "Ranked preferences must be consecutive starting from 1."
                )

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
        self, voter_id: UUID, vote_name: str, vote_type: str = "election"
    ) -> None:
        """Send a vote confirmation email to the voter."""
        if not self._email_service:
            logger.warning("Email service not configured, skipping vote confirmation email")
            return

        # Decrypt voter email
        voter = await self.voter_repo.get_voter_by_id(self.session, voter_id)
        await self._keys_manager.init_org_keys(self.session, org_id=None)
        args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

        from app.models.dto.voter import VoterDTO
        voter_dto = await self._mapper.decrypt_model(voter, VoterDTO, args, self.session)

        if not voter_dto.email:
            logger.warning("Voter has no email address", voter_id=str(voter_id))
            return

        self._email_service.send_vote_confirmation(voter_dto.email, vote_name, vote_type)
