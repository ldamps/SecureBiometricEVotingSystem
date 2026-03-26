import os

import structlog

from .base import BaseEncryption

logger = structlog.get_logger()


def get_encryption() -> BaseEncryption:
    """Return the configured encryption provider.

    Set ENCRYPTION_PROVIDER=aws_kms for production (requires KMS_KEY_ID,
    AWS_REGION, ENCRYPTION_HMAC_SECRET).  Defaults to local Fernet-based
    encryption for development (requires ENCRYPTION_KEY, ENCRYPTION_HMAC_SECRET).
    """
    provider = os.getenv("ENCRYPTION_PROVIDER", "local").lower()

    if provider == "aws_kms":
        from .aws_kms import AWSKMSEncryption

        key_id = os.environ["KMS_KEY_ID"]
        region = os.getenv("AWS_REGION", "us-east-1")
        hmac_secret = os.environ["ENCRYPTION_HMAC_SECRET"]
        return AWSKMSEncryption(key_id=key_id, region=region, hmac_secret=hmac_secret)

    from .local import LocalEncryption

    encryption_key = os.environ["ENCRYPTION_KEY"]
    hmac_secret = os.environ["ENCRYPTION_HMAC_SECRET"]
    logger.info("Using local Fernet encryption")
    return LocalEncryption(encryption_key=encryption_key, hmac_secret=hmac_secret)
