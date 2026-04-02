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
        """
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

            outputs = session.verified_outputs or {}
            dob = outputs.get("dob")
            address = outputs.get("address")

            return {
                "session_id": session.id,
                "verified": True,
                "extracted_data": {
                    "first_name": outputs.get("first_name") or "",
                    "last_name": outputs.get("last_name") or "",
                    "date_of_birth": (
                        f"{dob['day']:02d}/{dob['month']:02d}/{dob['year']}"
                        if dob and dob.get("day") and dob.get("month") and dob.get("year")
                        else ""
                    ),
                    "document_number": outputs.get("id_number") or "",
                    "document_type": outputs.get("id_number_type") or "",
                    "address": {
                        "line1": address.get("line1") or "",
                        "line2": address.get("line2") or "",
                        "city": address.get("city") or "",
                        "postal_code": address.get("postal_code") or "",
                        "country": address.get("country") or "",
                    } if address else None,
                },
            }
        except Exception:
            logger.exception("Failed to get verified outputs", session_id=session_id)
            raise

    async def get_verification_status(self, session_id: str) -> dict:
        """Retrieve the current status of a verification session.

        Returns a dict with `status` (requires_input | processing | verified | canceled)
        and the `last_error` if any.
        """
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
