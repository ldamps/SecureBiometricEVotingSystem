# app/application/api/v1/voter_route.py - Voter route definitions

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, File, Form, Path, UploadFile, status, HTTPException

from app.application.api.dependencies import (
    get_address_service,
    get_voter_ledger_service,
    get_voter_passport_service,
    get_voter_service,
    get_address_verification_dependencies,
)
from app.application.api.responses import responses
from app.application.constants import Resource
from app.models.dto.address import CreateAddressPlainDTO, UpdateAddressPlainDTO
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO
from app.models.dto.voter_ledger import CreateVoterLedgerPlainDTO, CreateVoterLedgerRequest
from app.models.dto.voter_passport import CreateVoterPassportPlainDTO, UpdateVoterPassportPlainDTO
from app.models.schemas.address import AddressItem, CreateAddress, UpdateAddress
from app.models.schemas.voter import (
    VoterItem,
    VoterRegistrationRequest,
    VoterUpdateRequest,
    VerifyIdentityRequest,
    VerifyIdentityResponse,
)
from app.models.schemas.voter_ledger import VoterLedgerItem
from app.models.schemas.voter_passport import (
    VoterPassportItem,
    CreateVoterPassportRequest,
    UpdateVoterPassportRequest,
)
from app.service.address_service import AddressService
from app.service.voter_ledger_service import VoterLedgerService
from app.service.voter_passport_service import VoterPassportService
from app.service.voter_service import VoterService

voter_responses = responses(Resource.VOTER)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/voter",
    tags=["voter"],
)


# Get voter details by voter ID
@router.get(
    "/{voter_id}",
    responses=voter_responses,
    status_code=status.HTTP_200_OK,
)
async def get_voter_by_voter_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterService = Depends(get_voter_service),
) -> VoterItem:
    """Get voter details by voter ID."""
    return await service.get_voter_by_id(voter_id)


# Register a new voter
@router.post(
    "/register",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_201_CREATED,
)
async def register_voter(
    body: VoterRegistrationRequest = Body(..., description="The voter registration request."),
    service: VoterService = Depends(get_voter_service),
):
    """Register a new voter.

    Requires either a national insurance number or at least one passport entry.
    """
    dto = RegisterVoterPlainDTO.create_dto(body)
    return await service.register_voter(
        dto,
        passport_entries=body.passports or None,
        kyc_session_id=body.kyc_session_id,
    )


# Update a voter's (registration) details
@router.patch(
    "/{voter_id}",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_200_OK,
)
async def update_voter(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: VoterUpdateRequest = Body(..., description="The voter update request."),
    service: VoterService = Depends(get_voter_service),
):
    """Update a voter's (registration) details."""
    dto = UpdateVoterPlainDTO.create_dto(body, voter_id)
    return await service.update_voter_details(voter_id, dto)


# Verify a voter's identity
@router.post(
    "/verify-identity",
    responses=voter_responses,
    response_model=VerifyIdentityResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_voter_identity(
    body: VerifyIdentityRequest = Body(..., description="The voter identity verification request."),
    service: VoterService = Depends(get_voter_service),
):
    """Verify a voter's identity by matching their name and address details against registered voters."""
    return await service.verify_voter_identity(body)


# Verify a voter's proof of address
@router.post(
    "/{voter_id}/verify-address",
    responses=voter_responses,
    status_code=status.HTTP_200_OK,
)
async def verify_proof_of_address(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    address_id: UUID = Form(..., description="The address ID to verify."),
    file: UploadFile = File(..., description="Proof of address document (PDF, JPG, PNG, max 10 MB)."),
    deps: tuple = Depends(get_address_verification_dependencies),
):
    """Verify a voter's proof of address using OCR.

    Extracts text from the uploaded document via Tesseract OCR and checks
    whether it matches the voter's registered address. On success the
    address status is updated to ACTIVE, the voter's constituency is
    assigned, and the voter is activated if all registration steps are complete.

    The uploaded file is held in memory only and is **never saved**.
    """
    from app.service.address_verification_service import extract_text, verify_address_in_text

    address_service, voter_service = deps

    # Validate voter exists
    await voter_service.voter_repo.get_voter_by_id(voter_service.session, voter_id)

    # Validate file type
    allowed_types = {"application/pdf", "image/jpeg", "image/png"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, JPG, PNG.",
        )

    # Read file into memory (max 10 MB)
    max_size = 10 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB.",
        )

    # Retrieve the stored address and decrypt it (validates voter ownership)
    address_item = await address_service.get_address_by_id(voter_id, address_id)

    # Already verified — return success so the voter can proceed without re-uploading
    if address_item.address_status == "ACTIVE":
        return {
            "status": "verified",
            "message": "Address has already been verified.",
            "matched_fields": 0,
            "total_fields": 0,
            "details": {},
            "address_status": "ACTIVE",
        }

    stored_line1 = address_item.address_line1 or ""
    stored_city = address_item.town or ""
    stored_postcode = address_item.postcode or ""

    if not stored_line1 and not stored_postcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The stored address has no verifiable fields (address_line1, postcode).",
        )

    logger.info(
        "verify_proof_of_address",
        voter_id=str(voter_id),
        address_id=str(address_id),
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
    )

    # Extract text via OCR
    extracted_text = extract_text(contents, file.content_type)

    # Compare against stored address fields
    result = verify_address_in_text(extracted_text, stored_line1, stored_city, stored_postcode)

    if result["passed"]:
        # Update address status to ACTIVE
        await address_service.address_repo.update_address_status(
            address_service.session, address_id, "ACTIVE"
        )

        # Sync constituency from postcode (UK) or set to Overseas
        if address_item.address_type == "OVERSEAS":
            await address_service._sync_voter_overseas_constituency(voter_id)
        elif address_item.postcode:
            await address_service._sync_voter_constituency(voter_id, address_item.postcode)

        # Try to activate voter if all steps are complete
        activated = await voter_service.activate_voter_if_ready(voter_id)

        logger.info(
            "address_verified_and_activated",
            voter_id=str(voter_id),
            address_id=str(address_id),
            voter_activated=activated,
        )

    return {
        "status": "verified" if result["passed"] else "failed",
        "message": (
            "Address verified — your document matches your registered address."
            if result["passed"]
            else "Address verification failed — the document does not match your registered address."
        ),
        "matched_fields": result["matched_fields"],
        "total_fields": result["total_fields"],
        "details": result["details"],
        "address_status": "ACTIVE" if result["passed"] else "PENDING",
    }


### VOTER ADDRESS ROUTES ###


# List voter's addresses
@router.get(
    "/{voter_id}/addresses",
    responses=voter_responses,
    response_model=List[AddressItem],
    status_code=status.HTTP_200_OK,
)
async def get_voter_addresses(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: AddressService = Depends(get_address_service),
):
    """Get all addresses for a voter."""
    return await service.get_all_addresses_by_voter_id(voter_id)


# Get an address by ID
@router.get(
    "/{voter_id}/address/{address_id}",
    responses=voter_responses,
    response_model=AddressItem,
    status_code=status.HTTP_200_OK,
)
async def get_voter_address_by_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    address_id: UUID = Path(..., description="The unique identifier for the address."),
    service: AddressService = Depends(get_address_service),
):
    """Get an address by ID."""
    return await service.get_address_by_id(voter_id, address_id)


# Create a new address for a voter
@router.post(
    "/{voter_id}/address",
    responses=voter_responses,
    response_model=AddressItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_voter_address(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: CreateAddress = Body(..., description="The address creation request."),
    service: AddressService = Depends(get_address_service),
):
    """Create a new address for a voter.

    If the address type is LOCAL_CURRENT, the voter's constituency is
    automatically resolved from the county field and any existing current
    address is demoted to PAST.
    """
    dto = CreateAddressPlainDTO.create_dto(body)
    dto.voter_id = voter_id
    return await service.create_address(dto)


# Update an address for a voter
@router.patch(
    "/{voter_id}/address/{address_id}",
    responses=voter_responses,
    response_model=AddressItem,
    status_code=status.HTTP_200_OK,
)
async def update_voter_address(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    address_id: UUID = Path(..., description="The unique identifier for the address."),
    body: UpdateAddress = Body(..., description="The address update request."),
    service: AddressService = Depends(get_address_service),
):
    """Update an address for a voter.

    If the county changes on a LOCAL_CURRENT address the voter's
    constituency is automatically re-resolved.
    """
    dto = UpdateAddressPlainDTO.create_dto(body, address_id)
    dto.voter_id = voter_id
    return await service.update_address(dto)


# Delete an address for a voter
@router.delete(
    "/{voter_id}/address/{address_id}",
    responses=voter_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_voter_address(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    address_id: UUID = Path(..., description="The unique identifier for the address."),
    service: AddressService = Depends(get_address_service),
):
    """Delete an address for a voter.

    Current local addresses (LOCAL_CURRENT) cannot be deleted — create a
    new current address first, which will automatically demote the old one.
    """
    await service.delete_address(voter_id, address_id)


### VOTER PASSPORT ROUTES ###


# List voter's passports
@router.get(
    "/{voter_id}/passports",
    responses=voter_responses,
    response_model=List[VoterPassportItem],
    status_code=status.HTTP_200_OK,
)
async def get_voter_passports(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterPassportService = Depends(get_voter_passport_service),
):
    """Get all passport entries for a voter."""
    return await service.get_all_passports_by_voter_id(voter_id)


# Get a passport by ID
@router.get(
    "/{voter_id}/passport/{passport_id}",
    responses=voter_responses,
    response_model=VoterPassportItem,
    status_code=status.HTTP_200_OK,
)
async def get_voter_passport_by_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    passport_id: UUID = Path(..., description="The unique identifier for the passport entry."),
    service: VoterPassportService = Depends(get_voter_passport_service),
):
    """Get a passport entry by ID."""
    return await service.get_passport_by_id(voter_id, passport_id)


# Create a new passport entry for a voter
@router.post(
    "/{voter_id}/passport",
    responses=voter_responses,
    response_model=VoterPassportItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_voter_passport(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: CreateVoterPassportRequest = Body(..., description="The passport creation request."),
    service: VoterPassportService = Depends(get_voter_passport_service),
):
    """Create a new passport entry for a voter."""
    dto = CreateVoterPassportPlainDTO.create_dto(body, voter_id)
    return await service.create_passport(dto)


# Update a passport entry for a voter
@router.patch(
    "/{voter_id}/passport/{passport_id}",
    responses=voter_responses,
    response_model=VoterPassportItem,
    status_code=status.HTTP_200_OK,
)
async def update_voter_passport(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    passport_id: UUID = Path(..., description="The unique identifier for the passport entry."),
    body: UpdateVoterPassportRequest = Body(..., description="The passport update request."),
    service: VoterPassportService = Depends(get_voter_passport_service),
):
    """Update a passport entry for a voter."""
    dto = UpdateVoterPassportPlainDTO.create_dto(body, passport_id, voter_id)
    return await service.update_passport(dto)


# Delete a passport entry for a voter
@router.delete(
    "/{voter_id}/passport/{passport_id}",
    responses=voter_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_voter_passport(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    passport_id: UUID = Path(..., description="The unique identifier for the passport entry."),
    service: VoterPassportService = Depends(get_voter_passport_service),
):
    """Delete a passport entry for a voter."""
    await service.delete_passport(voter_id, passport_id)


### VOTER LEDGER ROUTES ###


# Get a voter ledger entry by ID
@router.get(
    "/{voter_id}/ledger/{voter_ledger_id}",
    responses=voter_responses,
    response_model=VoterLedgerItem,
    status_code=status.HTTP_200_OK,
)
async def get_voter_ledger_entry_by_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    voter_ledger_id: UUID = Path(..., description="The unique identifier for the voter ledger entry."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
):
    """Get a voter ledger entry by ID."""
    return await service.get_voter_ledger_entry_by_id(voter_id, voter_ledger_id)


# List voter's ledger entries
@router.get(
    "/{voter_id}/ledger",
    responses=voter_responses,
    response_model=List[VoterLedgerItem],
    status_code=status.HTTP_200_OK,
)
async def get_voter_ledger_entries(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
):
    """Get all voter ledger entries for a voter."""
    return await service.get_all_voter_ledger_entries_by_voter_id(voter_id)


# Create voter ledger entry
@router.post(
    "/{voter_id}/ledger",
    responses=voter_responses,
    response_model=VoterLedgerItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_voter_ledger_entry(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: CreateVoterLedgerRequest = Body(..., description="The voter ledger creation request."),
    service: VoterLedgerService = Depends(get_voter_ledger_service),
):
    """Create a voter ledger entry."""
    dto = CreateVoterLedgerPlainDTO.create_dto(body, voter_id)
    return await service.create_voter_ledger(dto)

### VOTER ELIGIBILITY ROUTES ###

# Check voter eligibility
@router.get(
    "/{voter_id}/registration-status",
    responses=voter_responses,
    status_code=status.HTTP_200_OK,
)
async def get_registration_status(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterService = Depends(get_voter_service),
):
    """Check the voter's registration progress.

    Returns the current voter_status, whether address is verified,
    and whether biometrics are enrolled.
    """
    voter = await service.voter_repo.get_voter_by_id(service.session, voter_id)
    addresses = await service.address_repo.get_all_addresses_by_voter_id(
        service.session, voter_id
    )
    credentials = await service._biometric_credentials_repo.list_by_voter(
        service.session, voter_id
    )

    from app.models.sqlalchemy.address import AddressStatus
    has_active_address = any(
        a.address_status == AddressStatus.ACTIVE for a in addresses
    )
    has_biometric = any(c.is_active for c in credentials)

    return {
        "voter_id": str(voter_id),
        "voter_status": voter.voter_status,
        "registration_status": voter.registration_status,
        "address_verified": has_active_address,
        "biometric_enrolled": has_biometric,
        "ready": voter.voter_status == "ACTIVE",
        "steps_remaining": [
            step for step, done in [
                ("address_verification", has_active_address),
                ("biometric_enrollment", has_biometric),
            ] if not done
        ],
    }
