"""KYC identity verification routes."""

import structlog
from fastapi import APIRouter, Body, Path, status

from app.models.schemas.kyc import (
    CreateKYCSessionRequest,
    CreateKYCSessionResponse,
    KYCStatusResponse,
    KYCVerifiedOutputsResponse,
)
from app.service.kyc_service import KYCService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/kyc",
    tags=["kyc"],
)

_kyc_service = KYCService()

# create kyc session
@router.post(
    "/session",
    response_model=CreateKYCSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_kyc_session(
    body: CreateKYCSessionRequest = Body(..., description="KYC session creation request."),
):
    """Create a new Stripe Identity verification session."""
    result = await _kyc_service.create_verification_session(
        email=body.email,
        allowed_document_types=body.allowed_document_types,
    )
    return CreateKYCSessionResponse(**result)

# get kyc verified data
@router.get(
    "/session/{session_id}/verified-data",
    response_model=KYCVerifiedOutputsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_kyc_verified_data(
    session_id: str = Path(..., description="The Stripe VerificationSession ID."),
):
    """Get the extracted/verified data from a completed verification session."""
    result = await _kyc_service.get_verified_outputs(session_id)
    return KYCVerifiedOutputsResponse(**result)

# get kyc status
@router.get(
    "/session/{session_id}/status",
    response_model=KYCStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_kyc_status(
    session_id: str = Path(..., description="The Stripe VerificationSession ID."),
):
    """Get the current status of a KYC verification session."""
    result = await _kyc_service.get_verification_status(session_id)
    return KYCStatusResponse(**result)
