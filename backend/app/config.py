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

# Encryption
# ENCRYPTION_PROVIDER: "local" (default, Fernet) or "aws_kms"
ENCRYPTION_PROVIDER = os.getenv("ENCRYPTION_PROVIDER", "local")

# Local Fernet key — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# HMAC secret for deterministic search tokens (both providers)
ENCRYPTION_HMAC_SECRET = os.getenv("ENCRYPTION_HMAC_SECRET", "")

# AWS KMS (required when ENCRYPTION_PROVIDER=aws_kms)
KMS_KEY_ID = os.getenv("KMS_KEY_ID", "")        # e.g. arn:aws:kms:us-east-1:123456789012:key/...
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
