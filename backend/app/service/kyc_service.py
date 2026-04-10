"""KYC identity verification via Stripe Identity."""

import structlog
import stripe
from app.config import STRIPE_SECRET_KEY

logger = structlog.get_logger()

stripe.api_key = STRIPE_SECRET_KEY


class KYCService:
    """Creates and retrieves Stripe Identity verification sessions."""

    async def create_verification_session(
        self,
        email: str | None = None,
        allowed_document_types: list[str] | None = None,
    ) -> dict:
        """Create a Stripe Identity VerificationSession.

        Returns a dict with `session_id` and `client_secret` for the
        frontend to mount the embedded verification UI.

        In test mode (Stripe Identity unavailable), returns a mock session
        so the registration flow can be exercised end-to-end.
        """
        if self._is_test_mode or not STRIPE_SECRET_KEY:
            import uuid

            mock_id = f"mock_vs_{uuid.uuid4().hex[:16]}"
            logger.warning(
                "Stripe test/unconfigured mode: returning mock KYC session",
                session_id=mock_id,
            )
            return {
                "session_id": mock_id,
                "client_secret": f"mock_secret_{mock_id}",
            }

        valid_types = {"passport", "driving_license", "id_card"}
        doc_types = [t for t in (allowed_document_types or []) if t in valid_types]
        if not doc_types:
            doc_types = ["passport", "driving_license", "id_card"]

        try:
            session = stripe.identity.VerificationSession.create(
                type="document",
                metadata={"email": email or ""},
                options={
                    "document": {
                        "allowed_types": doc_types,
                        "require_matching_selfie": True,
                    },
                },
            )
            logger.info("KYC verification session created", session_id=session.id)
            return {
                "session_id": session.id,
                "client_secret": session.client_secret,
            }
        except Exception:
            logger.exception("Failed to create KYC verification session")
            raise

    async def get_verified_outputs(self, session_id: str) -> dict:
        """Retrieve the verified data extracted from the identity document.

        Only available when the session status is 'verified'.
        Returns extracted fields: first_name, last_name, date_of_birth,
        document_number, address, and document_type.
        """
        if session_id.startswith("mock_vs_"):
            logger.warning("Stripe test mode: returning mock verified outputs", session_id=session_id)
            return {
                "session_id": session_id,
                "verified": True,
                "extracted_data": {
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": "01/01/2000",
                    "document_number": "MOCK123456",
                    "document_type": "passport",
                    "address": {
                        "line1": "1 Test Street",
                        "line2": "",
                        "city": "Aberdeen",
                        "postal_code": "AB1 1AA",
                        "country": "GB",
                    },
                },
            }

        try:
            session = stripe.identity.VerificationSession.retrieve(
                session_id,
                expand=["verified_outputs"],
            )
            if session.status != "verified":
                return {
                    "session_id": session.id,
                    "verified": False,
                    "extracted_data": None,
                }

            outputs = session.verified_outputs
            if not outputs:
                return {
                    "session_id": session.id,
                    "verified": True,
                    "extracted_data": None,
                }

            # Stripe returns StripeObject — use getattr, not .get()
            dob = getattr(outputs, "dob", None)
            address = getattr(outputs, "address", None)

            dob_str = ""
            if dob:
                day = getattr(dob, "day", None)
                month = getattr(dob, "month", None)
                year = getattr(dob, "year", None)
                if day and month and year:
                    dob_str = f"{day:02d}/{month:02d}/{year}"

            address_data = None
            if address:
                address_data = {
                    "line1": getattr(address, "line1", "") or "",
                    "line2": getattr(address, "line2", "") or "",
                    "city": getattr(address, "city", "") or "",
                    "postal_code": getattr(address, "postal_code", "") or "",
                    "country": getattr(address, "country", "") or "",
                }

            return {
                "session_id": session.id,
                "verified": True,
                "extracted_data": {
                    "first_name": getattr(outputs, "first_name", "") or "",
                    "last_name": getattr(outputs, "last_name", "") or "",
                    "date_of_birth": dob_str,
                    "document_number": getattr(outputs, "id_number", "") or "",
                    "document_type": getattr(outputs, "id_number_type", "") or "",
                    "address": address_data,
                },
            }
        except Exception:
            logger.exception("Failed to get verified outputs", session_id=session_id)
            raise

    @property
    def _is_test_mode(self) -> bool:
        """True when running against Stripe test keys.

        In test mode Stripe Identity always returns dummy data
        ("Jenny Rosen"), so strict name/DOB comparison is skipped.
        """
        return (STRIPE_SECRET_KEY or "").startswith("sk_test_")

    async def validate_kyc_for_registration(
        self,
        session_id: str,
        first_name: str,
        surname: str,
        date_of_birth: str | None = None,
    ) -> dict:
        """Validate that a KYC session is verified and the extracted data
        matches the registration details the voter submitted.

        In Stripe test mode the name/DOB comparison is skipped because
        Stripe always returns dummy identity data.

        Returns the full extracted data on success.
        Raises ValueError if the session is not verified or the data does not match.
        """
        result = await self.get_verified_outputs(session_id)
        if not result.get("verified"):
            raise ValueError(
                "KYC session is not verified. The voter must complete identity "
                "verification before registering."
            )

        extracted = result.get("extracted_data") or {}

        # Mock sessions or Stripe test mode — skip strict comparison
        if session_id.startswith("mock_vs_") or self._is_test_mode:
            logger.warning(
                "Mock/test mode: skipping KYC name/DOB comparison",
                session_id=session_id,
            )
            return extracted

        kyc_first = (extracted.get("first_name") or "").strip().lower()
        kyc_last = (extracted.get("last_name") or "").strip().lower()

        reg_first = first_name.strip().lower()
        reg_surname = surname.strip().lower()

        if kyc_first != reg_first:
            raise ValueError(
                f"KYC first name '{extracted.get('first_name')}' does not match "
                f"registration first name '{first_name}'."
            )
        if kyc_last != reg_surname:
            raise ValueError(
                f"KYC last name '{extracted.get('last_name')}' does not match "
                f"registration surname '{surname}'."
            )

        if date_of_birth and extracted.get("date_of_birth"):
            kyc_dob = extracted["date_of_birth"].strip()
            reg_dob = date_of_birth.strip()
            if kyc_dob and reg_dob and kyc_dob != reg_dob:
                raise ValueError(
                    f"KYC date of birth '{kyc_dob}' does not match "
                    f"registration date of birth '{reg_dob}'."
                )

        logger.info(
            "KYC validation passed for registration",
            session_id=session_id,
        )
        return extracted

    async def get_verification_status(self, session_id: str) -> dict:
        """Retrieve the current status of a verification session.

        Returns a dict with `status` (requires_input | processing | verified | canceled)
        and the `last_error` if any.
        """
        if session_id.startswith("mock_vs_"):
            logger.warning("Stripe test mode: returning mock verified status", session_id=session_id)
            return {
                "session_id": session_id,
                "status": "verified",
                "last_error": None,
            }

        try:
            session = stripe.identity.VerificationSession.retrieve(session_id)
            return {
                "session_id": session.id,
                "status": session.status,
                "last_error": getattr(session, "last_error", None),
            }
        except Exception:
            logger.exception("Failed to get KYC verification status", session_id=session_id)
            raise
