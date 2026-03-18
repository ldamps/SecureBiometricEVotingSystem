import structlog
from app.config import AWS_REGION, KMS_KEY_ID
from app.infra.encryption.factory import get_encryption
from app.repository.keys_manager_repo import KeysManagerRepository
from app.repository.voter_repo import VoterRepository
from app.service.encryption_mapper_service import EncryptionMapperService
from app.service.encryption_service import EncryptionService
from app.service.keys_manager_service import KeysManagerService
from app.service.voter_service import VoterService
from app.models.sqlalchemy.voter import Voter
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from sqlalchemy.exc import IntegrityError, DBAPIError


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
        voter_repo=VoterRepository(),
        session=session,
        keys_manager=keys_manager,
        encryption_mapper=mapper,
    )



# ------------------------------------------------------------


# CODE DEPENDENCIES ----------


# ------------------------------------------------------------


# APP REPOSITORIES ----------


# ------------------------------------------------------------
