"""Alembic env.py: use app.config for URL and Base.metadata for autogenerate."""

import os
import sys

# Add project root so "app" is importable
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import DATABASE_URL
from app.models.base.sqlalchemy_base import Base

# Import all models so Base.metadata has every table (for autogenerate and create_all)
from app.models.sqlalchemy import (  # noqa: F401
    Address,
    AuditLog,
    BallotToken,
    BiometricChallenge,
    Candidate,
    Constituency,
    DeviceCredential,
    Election,
    ElectionOfficial,
    EncryptionKey,
    ErrorReport,
    Investigation,
    Party,
    Referendum,
    ReferendumVote,
    SeatAllocation,
    TallyResult,
    Voter,
    VoterLedger,
    Vote,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL only, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
