# candidate_service.py - Service layer for candidate-related operations.

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.application.core.exceptions import ValidationError
from app.models.dto.candidate import (
    CreateCandidatePlainDTO,
    CreateCandidateEncryptedDTO,
    CandidateDTO,
)
from app.models.schemas.candidate import CandidateItem
from app.models.sqlalchemy.audit_log import AuditLog
from app.repository.audit_log_repo import AuditLogRepository
from app.repository.candidate_repo import CandidateRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService

logger = structlog.get_logger()


class CandidateService(EncryptionUtilsMixin):
    """Service layer for candidate-related operations."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
        audit_log_repo: AuditLogRepository | None = None,
    ):
        self.candidate_repo = candidate_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper
        self._audit_log_repo = audit_log_repo or AuditLogRepository()

    async def create_candidate(self, dto: CreateCandidatePlainDTO) -> CandidateItem:
        """Create a new candidate.

        Validates that the party does not already have a candidate
        in this constituency for this election before inserting.
        """
        try:
            existing = await self.candidate_repo.get_candidate_by_election_and_party(
                self.session, dto.election_id, dto.constituency_id, dto.party_id,
            )
            if existing:
                raise ValidationError(
                    f"Party already has a candidate in this constituency for this election"
                )

            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            enc_row = await self._mapper.encrypt_dto(
                dto, CreateCandidateEncryptedDTO, args, self.session
            )
            candidate = enc_row.to_model()
            candidate = await self.candidate_repo.create_candidate(self.session, candidate)

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="CANDIDATE_ADDED",
                    action="CREATE",
                    summary=f"Candidate added to election {dto.election_id}",
                    resource_type="candidate",
                    resource_id=candidate.id,
                    election_id=dto.election_id,
                    actor_type="OFFICIAL",
                ),
            )

            return await self.candidate_model_to_schema_item(candidate, self.session)
        except Exception:
            logger.exception("Failed to create candidate", dto=dto)
            raise

    async def get_candidate_by_id(self, candidate_id: UUID) -> CandidateItem:
        """Get a candidate by its ID."""
        try:
            candidate = await self.candidate_repo.get_candidate_by_id(self.session, candidate_id)
            return await self.candidate_model_to_schema_item(candidate, self.session)
        except Exception:
            logger.exception("Failed to get candidate by ID", candidate_id=candidate_id)
            raise

    async def get_candidates_by_election(self, election_id: UUID) -> List[CandidateItem]:
        """Get all candidates for an election."""
        try:
            candidates = await self.candidate_repo.get_candidates_by_election_id(self.session, election_id)
            return [
                await self.candidate_model_to_schema_item(c, self.session)
                for c in candidates
            ]
        except Exception:
            logger.exception("Failed to get candidates by election", election_id=election_id)
            raise

    async def get_candidates_by_party(self, party_id: UUID) -> List[CandidateItem]:
        """Get all candidates belonging to a party."""
        try:
            candidates = await self.candidate_repo.get_candidates_by_party_id(self.session, party_id)
            return [
                await self.candidate_model_to_schema_item(c, self.session)
                for c in candidates
            ]
        except Exception:
            logger.exception("Failed to get candidates by party", party_id=party_id)
            raise

    async def update_candidate(self, candidate_id: UUID, update_data: dict) -> CandidateItem:
        """Update a candidate's mutable fields."""
        try:
            updated = await self.candidate_repo.update_candidate(
                self.session, candidate_id, update_data
            )

            await self._audit_log_repo.create_audit_log(
                self.session,
                AuditLog(
                    event_type="CANDIDATE_UPDATED",
                    action="UPDATE",
                    summary=f"Candidate {candidate_id} updated",
                    resource_type="candidate",
                    resource_id=candidate_id,
                    actor_type="OFFICIAL",
                ),
            )

            return await self.candidate_model_to_schema_item(updated, self.session)
        except Exception:
            logger.exception("Failed to update candidate", candidate_id=candidate_id)
            raise
