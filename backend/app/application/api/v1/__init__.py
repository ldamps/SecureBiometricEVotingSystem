# app/application/api/v1/__init__.py - V1 API router assembly

from app.application.api.versioning import (
    APIVersion,
    create_versioned_router,
    version_manager,
)
from app.application.api.v1 import health, voter_route, constituency_route

# Build the v1 router and include all v1 sub-routers
v1_router = create_versioned_router(APIVersion.V1, "")
v1_router.include_router(health.router)
v1_router.include_router(voter_route.router)
v1_router.include_router(constituency_route.router)

version_manager.register_version(APIVersion.V1, v1_router)
