"""Application configuration (env-based)."""

import os

from dotenv import load_dotenv

load_dotenv()

# Database: use postgresql+psycopg2 for sync (Alembic, create_all, Session).
# Example: postgresql://user:password@localhost:5432/secure_evoting
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/secure_evoting",
)
