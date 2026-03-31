# app/application/api/v1/voter_route.py - Voter route definitions

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Body, Depends, Path, status

from app.application.api.dependencies import (
    get_address_service,
    get_voter_ledger_service,
    get_voter_passport_service,
    get_voter_service,
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
    return await service.register_voter(dto, passport_entries=body.passports or None)


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
