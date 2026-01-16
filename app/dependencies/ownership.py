"""Ownership validation dependency"""

from fastapi import Depends
from app.database import get_db_connection
from app.services.ownership_validator import OwnershipValidator
from app.dependencies.auth import get_current_user
from app.models.inspector import Inspector


def get_ownership_validator(
    conn=Depends(get_db_connection), current_user: Inspector = Depends(get_current_user)
) -> OwnershipValidator:
    """Dependency to provide OwnershipValidator instance with current user"""
    return OwnershipValidator(conn, current_user)
