"""One-shot diagnostic — run inside the backend container to find
exactly what is broken in the voter registration flow."""

import asyncio
import json
import os
import sys
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
        elif key in ("AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "ENCRYPTION_KEY", "JWT_SECRET", "STRIPE_SECRET_KEY", "ENCRYPTION_HMAC_SECRET"):
            print(f"  OK:      {key} = {val[:8]}...")
        else:
            print(f"  OK:      {key} = {val}")

    # ── 2. Database connection ────────────────────────────────────
    print("\n[2] Database connection")
    try:
        from sqlalchemy import text
        from app.application.database import async_engine
        async with async_engine.connect() as conn:
            row = await conn.execute(text("SELECT 1"))
            print("  OK: database connection works")
    except Exception:
        print("  FAIL: database connection")
        traceback.print_exc()
        return

    # ── 3. Tables exist ───────────────────────────────────────────
    print("\n[3] Database tables")
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [r[0] for r in result.fetchall()]
            print(f"  Tables ({len(tables)}): {', '.join(tables)}")
            if "voters" not in tables:
                print("  FAIL: 'voters' table does not exist!")
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
            print(f"  OK: KMS encrypt works (key={os.getenv('KMS_KEY_ID', '')[:30]}...)")
            # Try decrypt
            resp2 = client.decrypt(CiphertextBlob=resp["CiphertextBlob"])
            print(f"  OK: KMS decrypt works")
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

    # ── 5. Full registration dry-run ──────────────────────────────
    print("\n[5] Full registration dry-run")
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

        from app.models.dto.voter import RegisterVoterPlainDTO
        dto = RegisterVoterPlainDTO.create_dto(body)
        print(f"  OK: DTO created (first_name={dto.first_name})")

        from app.service.base.encryption_utils_mixin import prepare_voter_registration_plain_fields
        plain_fields = prepare_voter_registration_plain_fields(dto)
        print(f"  OK: plain fields prepared (voter_ref={plain_fields.get('voter_reference', 'N/A')})")

        # Test encryption mapper
        from app.application.database import async_session_factory
        from app.service.keys_manager_service import KeysManagerService
        from app.service.encryption_mapper_service import EncryptionMapperService
        from app.models.dto.voter import RegisterVoterEncryptedDTO

        async with async_session_factory() as session:
            keys_mgr = KeysManagerService()
            mapper = EncryptionMapperService()

            await keys_mgr.init_org_keys(session, org_id=None)
            print("  OK: org keys initialised")

            args = await keys_mgr.build_encryption_args(session, org_id=None)
            print("  OK: encryption args built")

            plain = RegisterVoterPlainDTO(**plain_fields)
            enc_row = await mapper.encrypt_dto(plain, RegisterVoterEncryptedDTO, args, session)
            print("  OK: DTO encrypted successfully")

            voter = enc_row.to_model()
            voter.kyc_session_id = "mock_vs_diag123"
            print(f"  OK: voter model created (ref token exists: {bool(voter.voter_reference_search_token)})")

            # Don't actually insert — just confirm everything up to the DB write works
            await session.rollback()

        print("\n  === ALL CHECKS PASSED ===")
        print("  The registration flow works up to the DB insert.")
        print("  If you still get 500s, the issue is in the DB write (constraints/duplicates).")

    except Exception:
        print("  FAIL: registration dry-run")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
