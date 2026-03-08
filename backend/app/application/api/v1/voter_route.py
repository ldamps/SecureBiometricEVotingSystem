# app/application/api/v1/voter_route.py - Voter route definitions

from fastapi import APIRouter, status
from app.application.api.responses import responses
from app.application.constants import Resource
import structlog

voter_responses = responses(Resource.VOTER)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/voter",
    tags=["voter","voter_registration"],
)

# Get voter details by voter ID
@router.get(
    "/{voter_id}", 
    responses=voter_responses, 
    status_code=status.HTTP_200_OK
)
async def get_voter_by_voter_id(

):
    """
    Get voter details by voter ID
    """
    pass


# Get voter details by ...


# Register a new voter


# Update a voter's (registration) details


# Send registration confirmation email


