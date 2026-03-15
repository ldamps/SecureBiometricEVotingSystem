class BusinessLogicError(Exception):
    """Base class for business logic errors."""

class NotFoundError(BusinessLogicError):
    """Raised when a resource is not found/does not exist."""