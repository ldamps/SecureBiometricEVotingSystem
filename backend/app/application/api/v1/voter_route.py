# app/application/api/v1/voter_route.py - Voter route definitions

from fastapi import APIRouter, status, Path, Depends, Body
from app.application.api.responses import responses
from app.application.constants import Resource
from uuid import UUID
import structlog
from app.service.voter_service import VoterService
from app.application.api.dependencies import get_voter_service
from app.models.schemas.voter import VoterItem, VoterRegistrationRequest, VoterUpdateRequest
from app.models.dto.voter import RegisterVoterPlainDTO, UpdateVoterPlainDTO
from app.models.dto.address import CreateAddressPlainDTO
from app.service.address_service import AddressService
from app.application.api.dependencies import get_address_service
from app.models.schemas.address import CreateAddress, AddressItem
from typing import List

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
    status_code=status.HTTP_200_OK
)
async def get_voter_by_voter_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: VoterService = Depends(get_voter_service),
    address_service: AddressService = Depends(get_address_service),
) -> VoterItem:
    """
    Get voter details by voter ID
    """
    return await service.get_voter_by_id(voter_id)


# Register a new voter
@router.post(
    "/register",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_201_CREATED
)
async def register_voter(
    body: VoterRegistrationRequest = Body(..., description="The voter registration request."),
    service: VoterService = Depends(get_voter_service),
):
    """
    Register a new voter
    """
    dto = RegisterVoterPlainDTO.create_dto(body)
    return await service.register_voter(dto)


# Update a voter's (registration) details
@router.patch(
    "/{voter_id}",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_200_OK
)
async def update_voter(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: VoterUpdateRequest = Body(..., description="The voter update request."),
    service: VoterService = Depends(get_voter_service),
):
    """
    Update a voter's (registration) details
    """
    dto = UpdateVoterPlainDTO.create_dto(body, voter_id)
    return await service.update_voter_details(voter_id, dto)



# Verify a voter's identity
@router.post(
    "/{voter_id}/verify-identity",
    responses=voter_responses,
    response_model=VoterItem,
    status_code=status.HTTP_200_OK
)
async def verify_voter_identity(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
):
    """ Verify a voter's identity (i.e. their personal details) """
    pass



### VOTER ADDRESS ROUTES ###

# list voter's addresses
@router.get(
    "/{voter_id}/addresses",
    responses=voter_responses,
    response_model=List[AddressItem],
    status_code=status.HTTP_200_OK
)
async def get_voter_addresses(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    service: AddressService = Depends(get_address_service),
):
    """ Get all addresses for a voter """
    return await service.get_all_addresses_by_voter_id(voter_id)



# get an address by ID
@router.get(
    "/{voter_id}/address/{address_id}",
    responses=voter_responses,
    response_model=AddressItem,
    status_code=status.HTTP_200_OK
)
async def get_voter_address_by_id(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    address_id: UUID = Path(..., description="The unique identifier for the address."),
    service: AddressService = Depends(get_address_service),
):
    """ Get an address by ID """
    return await service.get_address_by_id(voter_id, address_id)


# create a new address for a voter
@router.post(
    "/{voter_id}/address",
    responses=voter_responses,
    response_model=AddressItem,
    status_code=status.HTTP_201_CREATED
)
async def create_voter_address(
    voter_id: UUID = Path(..., description="The unique identifier for the voter."),
    body: CreateAddress = Body(..., description="The address creation request."),
    service: AddressService = Depends(get_address_service),
):
    """ Create a new address for a voter """
    dto = CreateAddressPlainDTO.create_dto(body)
    return await service.create_address(dto)


# update an address for a voter


# delete an address for a voter


### VOTER BIOMETRIC TEMPLATE ROUTES ###



