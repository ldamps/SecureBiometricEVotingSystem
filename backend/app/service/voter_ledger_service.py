
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.voter_ledger_repo import VoterLedgerRepository
from app.service.base.encryption_utils_mixin import EncryptionUtilsMixin
from app.service.keys_manager_service import KeysManagerService
from app.service.encryption_mapper_service import EncryptionMapperService
from app.models.dto.voter_ledger import CreateVoterLedgerPlainDTO, CreateVoterLedgerEncryptedDTO, VoterLedgerDTO
from app.models.schemas.voter_ledger import VoterLedgerItem, ElectionVoterItem, ElectionVoterListResponse, ReferendumVoterListResponse
from uuid import UUID
from typing import List

logger = structlog.get_logger()


class VoterLedgerService(EncryptionUtilsMixin):
    """Service layer for voter-ledger related operations."""

    def __init__(
        self,
        voter_ledger_repo: VoterLedgerRepository,
        session: AsyncSession,
        keys_manager: KeysManagerService,
        encryption_mapper: EncryptionMapperService,
    ):
        self.voter_ledger_repo = voter_ledger_repo
        self.session = session
        self._keys_manager = keys_manager
        self._mapper = encryption_mapper

    async def create_voter_ledger(
        self,
        dto: CreateVoterLedgerPlainDTO,
    ) -> VoterLedgerItem:
        """Create a new voter ledger entry."""
        try:
            await self._keys_manager.init_org_keys(self.session, org_id=None)
            args = await self._keys_manager.build_encryption_args(self.session, org_id=None)

            encrypted_dto = await self._mapper.encrypt_dto(
                dto, CreateVoterLedgerEncryptedDTO, args, self.session
            )
            voter_ledger_model = encrypted_dto.to_model()
            voter_ledger = await self.voter_ledger_repo.create_voter_ledger(
                self.session, voter_ledger_model
            )

            voter_ledger_dto = await self._mapper.decrypt_model(
                voter_ledger, VoterLedgerDTO, args, self.session
            )
            return voter_ledger_dto.to_schema()

        except Exception:
            logger.exception("Failed to create voter ledger", dto=dto)
            raise

    async def get_voter_ledger_by_id(
        self,
        voter_id: UUID,
        voter_ledger_id: UUID,
    ) -> VoterLedgerItem:
        """Get a voter ledger entry by its ID."""
        try:
            voter_ledger = await self.voter_ledger_repo.get_voter_ledger_by_id(
                self.session, voter_ledger_id
            )
            return await self.voter_ledger_model_to_schema_item(voter_ledger, self.session)

        except Exception:
            logger.exception("Failed to get voter ledger by ID", voter_id=voter_id, voter_ledger_id=voter_ledger_id)
            raise

    async def get_all_voter_ledger_entries_by_voter_id(
        self,
        voter_id: UUID,
    ) -> List[VoterLedgerItem]:
        """Get all voter ledger entries for a voter."""
        try:
            voter_ledger = await self.voter_ledger_repo.get_all_voter_ledger_entries_by_voter_id(
                self.session, voter_id
            )
            return [await self.voter_ledger_model_to_schema_item(voter_ledger, self.session) for voter_ledger in voter_ledger]
            
        except Exception:
            logger.exception("Failed to get all voter ledger entries by voter ID", voter_id=voter_id)
            raise

    async def get_election_voters(
        self,
        election_id: UUID,
    ) -> ElectionVoterListResponse:
        """Get all voters for an election with their voting status."""
        try:
            ledger_entries = await self.voter_ledger_repo.get_all_voter_ledger_entries_by_election_id(
                self.session, election_id
            )

            voters: List[ElectionVoterItem] = []
            for entry in ledger_entries:
                voter = entry.voter
                voter_item = await self.voter_model_to_schema_item(voter, self.session)
                voters.append(ElectionVoterItem(
                    voter_id=str(entry.voter_id),
                    first_name=voter_item.first_name,
                    surname=voter_item.surname,
                    has_voted=entry.voted_at is not None,
                    voted_at=entry.voted_at,
                ))

            total_voted = sum(1 for v in voters if v.has_voted)

            return ElectionVoterListResponse(
                election_id=str(election_id),
                total_voters=len(voters),
                total_voted=total_voted,
                total_not_voted=len(voters) - total_voted,
                voters=voters,
            )

        except Exception:
            logger.exception("Failed to get election voters", election_id=election_id)
            raise

    async def get_referendum_voters(
        self,
        referendum_id: UUID,
    ) -> ReferendumVoterListResponse:
        """Get all voters for a referendum with their voting status."""
        try:
            ledger_entries = await self.voter_ledger_repo.get_all_voter_ledger_entries_by_referendum_id(
                self.session, referendum_id
            )

            voters: List[ElectionVoterItem] = []
            for entry in ledger_entries:
                voter = entry.voter
                voter_item = await self.voter_model_to_schema_item(voter, self.session)
                voters.append(ElectionVoterItem(
                    voter_id=str(entry.voter_id),
                    first_name=voter_item.first_name,
                    surname=voter_item.surname,
                    has_voted=entry.voted_at is not None,
                    voted_at=entry.voted_at,
                ))

            total_voted = sum(1 for v in voters if v.has_voted)

            return ReferendumVoterListResponse(
                referendum_id=str(referendum_id),
                total_voters=len(voters),
                total_voted=total_voted,
                total_not_voted=len(voters) - total_voted,
                voters=voters,
            )

        except Exception:
            logger.exception("Failed to get referendum voters", referendum_id=referendum_id)
            raise
