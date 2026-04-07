"""One-shot diagnostic — run inside the backend container to find
exactly what is broken in the voter registration flow."""

import asyncio
import os
import traceback


async def main():
    print("=" * 60)
    print("DIAGNOSTIC: voter registration flow")
    print("=" * 60)

    # ── 1. Environment variables ──────────────────────────────────
    print("\n[1] Environment variables")
    for key in [
        "DATABASE_URL", "ENCRYPTION_PROVIDER", "ENCRYPTION_KEY",
        "ENCRYPTION_HMAC_SECRET", "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION",
        "KMS_KEY_ID", "STRIPE_SECRET_KEY", "JWT_SECRET",
    ]:
        val = os.getenv(key, "")
        if not val:
            print(f"  MISSING: {key}")
        elif key in ("AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "ENCRYPTION_KEY",
                      "JWT_SECRET", "STRIPE_SECRET_KEY", "ENCRYPTION_HMAC_SECRET"):
            print(f"  OK:      {key} = {val[:8]}...")
        else:
            print(f"  OK:      {key} = {val}")

    # ── 2. Database connection ────────────────────────────────────
    print("\n[2] Database connection")
    try:
        from app.db import init_async_db
        session_factory = init_async_db()
        from sqlalchemy import text
        async with session_factory() as session:
            row = await session.execute(text("SELECT 1"))
            print("  OK: database connection works")
    except Exception:
        print("  FAIL: database connection")
        traceback.print_exc()
        return

    # ── 3. Tables exist ───────────────────────────────────────────
    print("\n[3] Database tables")
    try:
        async with session_factory() as session:
            result = await session.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [r[0] for r in result.fetchall()]
            print(f"  Tables ({len(tables)}): {', '.join(tables)}")
            if "voters" not in tables:
                print("  FAIL: 'voters' table does not exist!")
                return
            else:
                print("  OK: 'voters' table exists")
    except Exception:
        print("  FAIL: checking tables")
        traceback.print_exc()
        return

    # ── 4. Encryption (KMS or local) ─────────────────────────────
    print("\n[4] Encryption")
    try:
        from app.config import ENCRYPTION_PROVIDER
        print(f"  Provider: {ENCRYPTION_PROVIDER}")
        if ENCRYPTION_PROVIDER == "aws_kms":
            import boto3
            client = boto3.client("kms", region_name=os.getenv("AWS_REGION", "us-east-1"))
            resp = client.encrypt(
                KeyId=os.getenv("KMS_KEY_ID", ""),
                Plaintext=b"diagnostic-test",
            )
            print("  OK: KMS encrypt works")
            resp2 = client.decrypt(CiphertextBlob=resp["CiphertextBlob"])
            print("  OK: KMS decrypt works")
        else:
            from cryptography.fernet import Fernet
            key = os.getenv("ENCRYPTION_KEY", "")
            f = Fernet(key.encode())
            token = f.encrypt(b"test")
            f.decrypt(token)
            print("  OK: Local Fernet encryption works")
    except Exception:
        print("  FAIL: encryption")
        traceback.print_exc()

    # ── 5. Schema validation ──────────────────────────────────────
    print("\n[5] Schema validation")
    try:
        from app.models.schemas.voter import VoterRegistrationRequest
        body = VoterRegistrationRequest(
            kyc_session_id="mock_vs_diag123",
            first_name="Diag",
            surname="Test",
            date_of_birth="2000-06-15T00:00:00Z",
            email="diag@example.com",
            national_insurance_number="QQ123456C",
            passports=[],
            nationality_category="BRITISH_CITIZEN",
            renew_by="2027-04-07T00:00:00Z",
        )
        print("  OK: schema validation passed")
    except Exception:
        print("  FAIL: schema validation")
        traceback.print_exc()
        return

    # ── 6. Full registration (service layer) ──────────────────────
    print("\n[6] Full registration via service")
    try:
        from app.models.dto.voter import RegisterVoterPlainDTO
        from app.service.voter_service import VoterService
        from app.service.keys_manager_service import KeysManagerService
        from app.service.encryption_mapper_service import EncryptionMapperService
        from app.service.email_service import EmailService
        from app.repository.voter_repo import VoterRepository
        from app.repository.voter_passport_repo import VoterPassportRepository
        from app.repository.audit_log_repo import AuditLogRepository

        dto = RegisterVoterPlainDTO.create_dto(body)

        async with session_factory() as session:
            async with session.begin():
                service = VoterService(
                    voter_repo=VoterRepository(),
                    session=session,
                    keys_manager=KeysManagerService(),
                    mapper=EncryptionMapperService(),
                    email_service=None,
                )
                result = await service.register_voter(
                    dto,
                    passport_entries=None,
                    kyc_session_id="mock_vs_diag123",
                )
                print(f"  OK: voter registered! id={result.id}")
                # Roll back so we don't pollute the DB
                await session.rollback()
                print("  (rolled back — no data written)")

    except Exception:
        print("  FAIL: registration service")
        traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
