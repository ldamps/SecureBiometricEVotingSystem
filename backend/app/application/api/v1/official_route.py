# admin_route.py - Admin routes for the e-voting system (election officers + administrators)
from fastapi import APIRouter
from app.application.api.responses import responses
from app.application.constants import Resource
import structlog

official_responses = responses(Resource.OFFICIAL)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/official",
    tags=["official"],
)

# Create election official (only admins can create election officials)




# Update election official (officers can update their own details + admins can update any officer's details)


# Get all election officers


# Get all administrators


# Get election official by ID 


# Deactivate election officials (admins only)






