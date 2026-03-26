# app/application/api/v1/constituency_route.py - Read-only constituency endpoints.

from fastapi import APIRouter, status, Path, Depends, Query
from app.application.api.responses import responses
from app.application.constants import Resource
from uuid import UUID
import structlog
from typing import Optional

from app.service.constituency_service import ConstituencyService
from app.application.api.dependencies import get_constituency_service
from app.models.schemas.constituency import ConstituencyItem

constituency_responses = responses(Resource.CONSTITUENCY)
logger = structlog.get_logger()

### ROUTES ###
router = APIRouter(
    prefix="/constituency",
    tags=["Constituency"],
)


@router.get(
    "",
    response_model=list[ConstituencyItem],
    status_code=status.HTTP_200_OK,
    responses=constituency_responses["GET"],
    summary="List all constituencies",
    description="Returns all UK county constituencies. Optionally filter by country.",
)
async def list_constituencies(
    country: Optional[str] = Query(None, description="Filter by country (e.g. England, Scotland, Wales, Northern Ireland)"),
    service: ConstituencyService = Depends(get_constituency_service),
) -> list[ConstituencyItem]:
    if country:
        constituencies = await service.get_by_country(country)
    else:
        constituencies = await service.get_all()
    return [ConstituencyItem.model_validate(c, from_attributes=True) for c in constituencies]


@router.get(
    "/{constituency_id}",
    response_model=ConstituencyItem,
    status_code=status.HTTP_200_OK,
    responses=constituency_responses["GET"],
    summary="Get a constituency by ID",
    description="Returns a single constituency by its UUID.",
)
async def get_constituency(
    constituency_id: UUID = Path(..., description="The constituency UUID"),
    service: ConstituencyService = Depends(get_constituency_service),
) -> ConstituencyItem:
    constituency = await service.get_by_id(constituency_id)
    if not constituency:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constituency not found")
    return ConstituencyItem.model_validate(constituency, from_attributes=True)
