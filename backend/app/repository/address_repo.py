# address_repo.py - Repository layer for address-related operations.

from app.models.sqlalchemy.address import Address

class AddressRepository:
    """Address-specific repository operations."""

    def __init__(self):
        super().__init__(Address)

    # CRUD METHODS ----------

    # ------------------------------------------------------------
