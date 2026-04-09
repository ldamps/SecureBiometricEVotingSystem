# app/application/api/v1/email_verification_route.py - Email verification code routes

from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, status

from app.application.api.dependencies import (
    get_email_verification_service,
    get_voter_service,
)
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.schemas.email_verification import (
    SendCodeRequest,
    SendCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from app.service.email_verification_service import EmailVerificationService
from app.service.voter_service import VoterService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/email-verification",
    tags=["email-verification"],
)

voter_responses = responses(Resource.VOTER)


@router.post(
    "/send",
    responses=voter_responses,
    response_model=SendCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def send_verification_code(
    body: SendCodeRequest = Body(...),
    service: EmailVerificationService = Depends(get_email_verification_service),
    voter_service: VoterService = Depends(get_voter_service),
):
    """Send a 6-digit verification code to the voter's registered email."""
    voter_id = UUID(body.voter_id)
    voter = await voter_service.get_voter_by_id(voter_id)

    if not voter.email:
        return SendCodeResponse(
            sent=False,
            message="No email address on file. Please contact your local electoral office.",
        )

    try:
        await service.send_code(voter_id, voter.email)
    except Exception:
        logger.exception("Failed to send verification code", voter_id=body.voter_id)
        return SendCodeResponse(
            sent=False,
            message="Failed to send verification code. Please try again.",
        )

    return SendCodeResponse(
        sent=True,
        message="A verification code has been sent to your registered email address.",
    )


@router.post(
    "/verify",
    responses=voter_responses,
    response_model=VerifyCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_code(
    body: VerifyCodeRequest = Body(...),
    service: EmailVerificationService = Depends(get_email_verification_service),
):
    """Verify a 6-digit code submitted by the voter."""
    voter_id = UUID(body.voter_id)
    verified = await service.verify_code(voter_id, body.code)

    if verified:
        return VerifyCodeResponse(
            verified=True,
            message="Email verification successful.",
        )

    return VerifyCodeResponse(
        verified=False,
        message="Invalid or expired code. Please request a new one.",
    )
