# app/application/api/v1/__init__.py - V1 API router assembly

from app.application.api.versioning import (
    APIVersion,
    create_versioned_router,
    version_manager,
)
from app.application.api.v1 import health, voter_route, constituency_route, election_route, party_route, referendum_route, voting_route, biometric_route, official_route, investigation_route, audit_route, auth_route

# Build the v1 router and include all v1 sub-routers
v1_router = create_versioned_router(APIVersion.V1, "")
v1_router.include_router(health.router)
v1_router.include_router(voter_route.router)
v1_router.include_router(constituency_route.router)
v1_router.include_router(election_route.router)
v1_router.include_router(party_route.router)
v1_router.include_router(referendum_route.router)
v1_router.include_router(voting_route.router)
v1_router.include_router(biometric_route.router)
v1_router.include_router(official_route.router)
v1_router.include_router(investigation_route.router)
v1_router.include_router(audit_route.router)
v1_router.include_router(auth_route.router)

version_manager.register_version(APIVersion.V1, v1_router)
