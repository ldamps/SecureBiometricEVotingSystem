# app/application/api/v1/biometric_route.py - Biometric (match-on-device) routes

from fastapi import APIRouter, Depends, Body, Path, status
from uuid import UUID
from typing import List
import structlog

from app.application.api.responses import responses
from app.application.constants import Resource
from app.service.biometric_service import BiometricService
from app.application.api.dependencies import get_biometric_service
from app.models.schemas.biometric import (
    EnrollDeviceRequest,
    EnrollDeviceResponse,
    CreateChallengeRequest,
    CreateChallengeResponse,
    VerifyBiometricRequest,
    VerifyBiometricResponse,
    DeviceCredentialItem,
)

biometric_responses = responses(Resource.BIOMETRIC)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/biometric",
    tags=["biometric"],
)



@router.post(
    "/enroll",
    responses=biometric_responses,
    response_model=EnrollDeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_device(
    body: EnrollDeviceRequest = Body(..., description="Device enrollment payload with public key."),
    service: BiometricService = Depends(get_biometric_service),
):
    """Enrol a mobile device for biometric verification.

    The device sends its ECDSA P-256 public key (generated on-device and
    bound to a face + ear biometric match).  No biometric template data
    is sent or stored by the server.
    """
    return await service.enroll_device(body)



@router.post(
    "/challenge",
    responses=biometric_responses,
    response_model=CreateChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_challenge(
    body: CreateChallengeRequest = Body(..., description="Request a verification challenge."),
    service: BiometricService = Depends(get_biometric_service),
):
    """Issue a single-use cryptographic challenge for the voter's device.

    The device must perform a local biometric match and then sign this
    challenge with the enrolled private key.
    """
    return await service.create_challenge(body)


@router.post(
    "/verify",
    responses=biometric_responses,
    response_model=VerifyBiometricResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_biometric(
    body: VerifyBiometricRequest = Body(..., description="Signed challenge from the device."),
    service: BiometricService = Depends(get_biometric_service),
):
    """Verify the device's ECDSA signature over the issued challenge.

    A successful verification proves the voter performed a biometric
    match on their device — the server never sees the biometric data.
    """
    return await service.verify_biometric(body)



@router.get(
    "/{voter_id}/credentials",
    responses=biometric_responses,
    response_model=List[DeviceCredentialItem],
    status_code=status.HTTP_200_OK,
)
async def list_credentials(
    voter_id: UUID = Path(..., description="The voter's unique identifier."),
    service: BiometricService = Depends(get_biometric_service),
):
    """List all device credentials enrolled for a voter."""
    return await service.list_credentials(voter_id)


@router.delete(
    "/credentials/{credential_id}",
    responses=biometric_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_credential(
    credential_id: UUID = Path(..., description="The credential to revoke."),
    service: BiometricService = Depends(get_biometric_service),
):
    """Revoke (deactivate) a device credential."""
    await service.revoke_credential(credential_id)