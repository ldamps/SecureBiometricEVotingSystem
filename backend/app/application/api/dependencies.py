import structlog
from app.config import AWS_REGION, KMS_KEY_ID
from app.infra.encryption.factory import get_encryption
from app.repository.keys_manager_repo import KeysManagerRepository
from app.repository.voter_repo import VoterRepository
from app.repository.address_repo import AddressRepository
from app.repository.voter_passport_repo import VoterPassportRepository
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.encryption_service import EncryptionService
from app.service.keys_manager_service import KeysManagerService
from app.service.voter_service import VoterService
from app.service.address_service import AddressService
from app.service.voter_passport_service import VoterPassportService
from app.models.sqlalchemy.voter import Voter
from app.models.sqlalchemy.address import Address
from app.models.sqlalchemy.voter_passport import VoterPassport
from app.models.sqlalchemy.voter_ledger import VoterLedger
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from sqlalchemy.exc import IntegrityError, DBAPIError
from app.service.voter_ledger_service import VoterLedgerService
from app.repository.voter_ledger_repo import VoterLedgerRepository
from app.service.election_service import ElectionService
from app.repository.election_repo import ElectionRepository
from app.models.sqlalchemy.election import Election
from app.service.constituency_service import ConstituencyService
from app.repository.constituency_repo import ConstituencyRepository
from app.models.sqlalchemy.voter import Voter
from app.service.party_service import PartyService
from app.repository.party_repo import PartyRepository
from app.models.sqlalchemy.party import Party
from app.service.candidate_service import CandidateService
from app.repository.candidate_repo import CandidateRepository
from app.models.sqlalchemy.candidate import Candidate
from app.service.referendum_service import ReferendumService
from app.repository.referendum_repo import ReferendumRepository
from app.models.sqlalchemy.referendum import Referendum
from app.service.voting_service import VotingService
from app.repository.vote_repo import VoteRepository
from app.repository.referendum_vote_repo import ReferendumVoteRepository
from app.repository.ballot_token_repo import BallotTokenRepository
from app.repository.tally_result_repo import TallyResultRepository
from app.service.biometric_service import BiometricService
from app.repository.biometric_credentials_repo import BiometricCredentialsRepository
from app.repository.biometric_challenge_repo import BiometricChallengeRepository
from app.service.ballot_service import BallotTokenService
from app.models.sqlalchemy.ballot_token import BallotToken
from app.service.email_service import EmailService
from app.infra.email.client import ResendEmailClient
from app.service.official_service import OfficialService
from app.repository.official_repo import OfficialRepository
from app.service.error_report_service import ErrorReportService
from app.repository.error_report_repo import ErrorReportRepository
from app.service.investigation_service import InvestigationService
from app.repository.investigation_repo import InvestigationRepository
from app.service.audit_log_service import AuditLogService
from app.service.tally_service import TallyService
from app.service.result_service import ResultService
from app.repository.audit_log_repo import AuditLogRepository
from app.service.auth_service import AuthService
from app.models.dto.auth import TokenPayload
from app.application.core.exceptions import AuthenticationError, AuthorizationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


logger = structlog.get_logger()

# DATABASE DEPENDENCIES ----------
def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Return session factory from FastAPI app state."""
    factory = getattr(request.app.state, "session_factory", None)
    if not factory:
        raise RuntimeError("Database not initialized: session factory missing")
    return factory


async def get_session(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session (cached per request)."""
    async with session_factory() as session:
        yield session


async def get_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session inside a transaction block."""
    try:
        async with session.begin():
            yield session
    except IntegrityError:
        raise
    except DBAPIError:
        logger.exception("DBAPI error")
        raise
    except Exception:
        logger.exception("Unexpected database error")
        raise

# ------------------------------------------------------------


# UTILITY DEPENDENCIES ----------

# ------------------------------------------------------------


# APP SERVICES ----------

def get_email_service() -> EmailService:
    """Get the email service."""
    return EmailService(client=ResendEmailClient())


def get_keys_manager_service() -> KeysManagerService:
    """DEK lifecycle (system org_id=None for voter PII)."""
    return KeysManagerService(
        encryption=get_encryption(),
        keys_repo=KeysManagerRepository(),
        kms_key_id=KMS_KEY_ID or "local-dev",
        kms_key_region=AWS_REGION,
    )


def get_voter_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
    email_service: EmailService = Depends(get_email_service),
) -> VoterService:
    """Get a voter service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return VoterService(
        voter_repo=VoterRepository(Voter),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        email_service=email_service,
    )

def get_address_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> AddressService:
    """Get an address service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return AddressService(
        address_repo=AddressRepository(Address),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        constituency_repo=ConstituencyRepository(),
        voter_repo=VoterRepository(Voter),
    )

def get_voter_passport_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> VoterPassportService:
    """Get a voter passport service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return VoterPassportService(
        passport_repo=VoterPassportRepository(VoterPassport),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
    )

def get_voter_ledger_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> VoterLedgerService:
    """Get a voter ledger service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return VoterLedgerService(
        voter_ledger_repo=VoterLedgerRepository(VoterLedger),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
    )

def get_election_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> ElectionService:
    """Get an election service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return ElectionService(
        election_repo=ElectionRepository(Election),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
    )

def get_constituency_service(
    session: AsyncSession = Depends(get_db),
) -> ConstituencyService:
    """Get a constituency service (read-only, no encryption needed)."""
    return ConstituencyService(
        constituency_repo=ConstituencyRepository(),
        session=session,
    )

def get_party_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> PartyService:
    """Get a party service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return PartyService(
        party_repo=PartyRepository(Party),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        audit_log_repo=AuditLogRepository(),
    )

def get_candidate_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> CandidateService:
    """Get a candidate service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return CandidateService(
        candidate_repo=CandidateRepository(Candidate),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        audit_log_repo=AuditLogRepository(),
    )

def get_voting_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
    email_service: EmailService = Depends(get_email_service),
) -> VotingService:
    """Get a voting service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return VotingService(
        vote_repo=VoteRepository(),
        referendum_vote_repo=ReferendumVoteRepository(),
        ballot_token_repo=BallotTokenRepository(),
        voter_ledger_repo=VoterLedgerRepository(VoterLedger),
        tally_result_repo=TallyResultRepository(),
        election_repo=ElectionRepository(Election),
        referendum_repo=ReferendumRepository(Referendum),
        candidate_repo=CandidateRepository(),
        voter_repo=VoterRepository(Voter),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        email_service=email_service,
    )

def get_biometric_service(
    session: AsyncSession = Depends(get_db),
) -> BiometricService:
    """Get a biometric service (match-on-device, no encryption needed)."""
    return BiometricService(
        credentials_repo=BiometricCredentialsRepository(),
        challenge_repo=BiometricChallengeRepository(),
        voter_repo=VoterRepository(Voter),
        session=session,
    )

def get_ballot_token_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> BallotTokenService:
    """Get a ballot token service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return BallotTokenService(
        ballot_token_repo=BallotTokenRepository(),
        election_repo=ElectionRepository(Election),
        referendum_repo=ReferendumRepository(Referendum),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
    )

def get_official_service(
    session: AsyncSession = Depends(get_db),
) -> OfficialService:
    """Get an official service (EncryptedBytes handled at column level)."""
    return OfficialService(
        official_repo=OfficialRepository(),
        session=session,
    )

def get_error_report_service(
    session: AsyncSession = Depends(get_db),
) -> ErrorReportService:
    """Get an error report service (auto-opens investigation on create)."""
    return ErrorReportService(
        error_report_repo=ErrorReportRepository(),
        investigation_repo=InvestigationRepository(),
        session=session,
    )

def get_investigation_service(
    session: AsyncSession = Depends(get_db),
) -> InvestigationService:
    """Get an investigation service."""
    return InvestigationService(
        investigation_repo=InvestigationRepository(),
        session=session,
    )

def get_audit_log_service(
    session: AsyncSession = Depends(get_db),
) -> AuditLogService:
    """Get an audit log service (read-only queries + internal event logging)."""
    return AuditLogService(
        audit_log_repo=AuditLogRepository(),
        session=session,
    )

def get_referendum_service(
    session: AsyncSession = Depends(get_db),
    keys_manager: KeysManagerService = Depends(get_keys_manager_service),
) -> ReferendumService:
    """Get a referendum service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return ReferendumService(
        referendum_repo=ReferendumRepository(Referendum),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
        audit_log_repo=AuditLogRepository(),
    )



# ------------------------------------------------------------


def get_tally_service(
    session: AsyncSession = Depends(get_db),
) -> TallyService:
    """Get a tally service (read-only queries on tally results)."""
    return TallyService(
        tally_result_repo=TallyResultRepository(),
        session=session,
    )

def get_result_service(
    session: AsyncSession = Depends(get_db),
) -> ResultService:
    """Get a result service (aggregates tallies into election/referendum results)."""
    return ResultService(
        tally_result_repo=TallyResultRepository(),
        election_repo=ElectionRepository(Election),
        session=session,
    )


# AUTH DEPENDENCIES ----------

_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    session: AsyncSession = Depends(get_db),
) -> AuthService:
    """Get an auth service."""
    return AuthService(
        official_repo=OfficialRepository(),
        session=session,
        audit_log_repo=AuditLogRepository(),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> TokenPayload:
    """Extract and validate the JWT from the Authorization header.

    Returns the decoded token payload for the current request.
    Raises AuthenticationError if the token is missing or invalid.
    """
    if credentials is None:
        raise AuthenticationError("Missing authentication token")
    return AuthService.decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    """Dependency factory that restricts access to specific roles.

    Usage in a route:
        current_user: TokenPayload = Depends(require_role("ADMIN"))
    """
    async def _check(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Insufficient permissions. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return _check


# ------------------------------------------------------------
