from typing import Any, Dict
from http import HTTPMethod
from app.application.constants import Resource

def responses(resource: Resource) -> Dict[HTTPMethod, Dict[int, Dict[str, Any]]]:
    """Generate FastAPI response definitions for a resource and return a dictionary of HTTP methods and their responses."""

    resource_str: str = resource.value.lower()

    return {
        HTTPMethod.GET: {
            200: {"description": f"{resource_str} retrieved successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": f"Insufficient permissions to access {resource_str}"},
            404: {"description": f"{resource_str} not found"},
            422: {"description": "Validation error"},
        },
        HTTPMethod.POST: {
            201: {"description": f"{resource_str} created successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": f"Insufficient permissions to create {resource_str}"},
            409: {"description": f"{resource_str} with this identifier already exists"},
            422: {"description": "Validation error"},
        },
        HTTPMethod.PUT: {
            200: {"description": f"{resource_str} updated successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": f"Insufficient permissions to update {resource_str}"},
            404: {"description": f"{resource_str} not found"},
            422: {"description": "Validation error"},
        },
        HTTPMethod.PATCH: {
            200: {"description": f"{resource_str} updated successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": f"Insufficient permissions to update {resource_str}"},
            404: {"description": f"{resource_str} not found"},
            422: {"description": "Validation error"},
        },
        HTTPMethod.DELETE: {
            204: {"description": f"{resource_str} deleted successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": f"Insufficient permissions to delete {resource_str}"},
            404: {"description": f"{resource_str} not found"},
        },
    }
