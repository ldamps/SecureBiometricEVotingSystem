from .versioning import (
    version_manager,
    register_all_versions,
    APIVersion,
    create_versioned_router,
)
from .responses import responses

# Import routers for auto-registration pattern
from . import v1  # noqa: F401

__all__ = [
    "version_manager",
    "APIVersion",
    "create_versioned_router",
    "register_all_versions",
    "responses",
]
