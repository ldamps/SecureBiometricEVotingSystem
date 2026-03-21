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
from app.service.constituency_service import ConstituencyService
from app.repository.constituency_repo import ConstituencyRepository


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
) -> VoterService:
    """Get a voter service."""
    mapper = EncryptionMapperService(EncryptionService(), keys_manager)
    return VoterService(
        voter_repo=VoterRepository(Voter),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
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

def get_constituency_service(
    session: AsyncSession = Depends(get_db),
) -> ConstituencyService:
    """Get a constituency service (read-only, no encryption needed)."""
    return ConstituencyService(
        constituency_repo=ConstituencyRepository(),
        session=session,
    )

# ------------------------------------------------------------


# CODE DEPENDENCIES ----------


# ------------------------------------------------------------


# APP REPOSITORIES ----------


# ------------------------------------------------------------
