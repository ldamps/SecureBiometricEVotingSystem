# Versioning for E-Voting Backend 

from typing import Optional
from fastapi import APIRouter, FastAPI
from enum import Enum
import structlog

logger = structlog.get_logger()

class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"

class APIVersionManager:
    """Manages API versioning and router registration."""

    def __init__(self):
        self._routers: dict[APIVersion, APIRouter] = {}
        self._deprecated_versions: set[APIVersion] = set()
        self._deprecation_warnings: dict[APIVersion, str] = {}

    def register_version(
        self,
        version: APIVersion,
        router: APIRouter,
        deprecated: bool = False,
        deprecation_message: Optional[str] = None,
    ) -> None:
        """Register a router for a specific API version."""
        if version in self._routers:
            logger.warning("API version already registered", version=version.value)
            return

        self._routers[version] = router

        if deprecated:
            self._deprecated_versions.add(version)
            self._deprecation_warnings[version] = (
                deprecation_message or f"API version {version.value} is deprecated"
            )

        logger.info(
            "API version registered",
            version=version.value,
            deprecated=deprecated,
            routes_count=len(router.routes),
        )

    def get_router(self, version: APIVersion) -> Optional[APIRouter]:
        """Get router for a specific version."""
        return self._routers.get(version)

    def is_deprecated(self, version: APIVersion) -> bool:
        """Check if a version is deprecated."""
        return version in self._deprecated_versions

    def get_deprecation_message(self, version: APIVersion) -> Optional[str]:
        """Get deprecation message for a version."""
        return self._deprecation_warnings.get(version)

    def get_all_versions(self) -> list[APIVersion]:
        """Get all registered versions."""
        return list(self._routers.keys())

    def get_latest_version(self) -> Optional[APIVersion]:
        """Get the latest (non-deprecated) version."""
        non_deprecated = [v for v in self._routers.keys() if not self.is_deprecated(v)]
        if not non_deprecated:
            return None
        # Enum order represents version order
        return max(non_deprecated, key=lambda v: list(APIVersion).index(v))

    def get_api_info(self) -> dict:
        """Get comprehensive API version information."""
        versions = {}
        for version in self.get_all_versions():
            router = self.get_router(version)
            versions[version.value] = {
                "deprecated": self.is_deprecated(version),
                "deprecation_message": self.get_deprecation_message(version),
                "routes_count": len(router.routes) if router else 0,
                "prefix": f"/api/{version.value}",
            }

        latest = self.get_latest_version()
        return {
            "versions": versions,
            "latest_version": latest.value if latest else None,
            "total_versions": len(versions),
        }


# Global version manager instance
version_manager = APIVersionManager()


def create_versioned_router(
    version: APIVersion, prefix: str = "", tags: Optional[list[str]] = None
) -> APIRouter:
    """Create a versioned router with proper prefix and tags."""
    if tags is None:
        tags = [f"API {version.value.upper()}"]

    full_prefix = f"/api/{version.value}{prefix}"

    return APIRouter(
        prefix=full_prefix,
        tags=tags,
        # Default error responses
        responses={
            404: {"description": "Not found"},
            500: {"description": "Internal server error"},
        },
    )


def register_all_versions(app: FastAPI) -> None:
    """Register all versioned routers with the FastAPI app."""
    for version in version_manager.get_all_versions():
        router = version_manager.get_router(version)
        if router:
            app.include_router(router)
            logger.info(
                "Versioned router included in app",
                version=version.value,
                routes_count=len(router.routes),
            )

