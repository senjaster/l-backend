"""Plant aggregate models"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, computed_field
from app.models import ConflictDetail, ConflictError
from app.utils.claim_utils import is_claim_stale


# Read models (returned from GET endpoints)
class Facility(BaseModel):
    """Energy facility (part of plant) - read model"""

    id: UUID
    name: str
    is_deleted: bool = False
    equipment_ids: Optional[list[UUID]] = Field(default_factory=list)


class Plant(BaseModel):
    """Plant aggregate with facilities - read model"""

    id: UUID
    name: str
    claimed_by_device_id: Optional[UUID] = None
    claimed_by_user_id: Optional[int] = None
    claimed_at: Optional[datetime] = None
    is_deleted: bool = False
    server_modified_at: datetime
    facilities: list[Facility] = Field(default_factory=list)

    @computed_field
    @property
    def is_claim_stale(self) -> bool:
        """
        Indicates if the claim is stale (can be overridden by another user).
        A claim becomes stale at 3:00 AM Moscow time each day.
        """
        return is_claim_stale(self.claimed_at)


# List models
class PlantListItem(BaseModel):
    """Lightweight plant item for list view"""

    id: UUID
    name: str
    claimed_by_device_id: Optional[UUID] = None
    claimed_by_user_id: Optional[int] = None
    claimed_at: Optional[datetime] = None
    is_deleted: bool = False
    server_modified_at: datetime

    @computed_field
    @property
    def is_claim_stale(self) -> bool:
        """
        Indicates if the claim is stale (can be overridden by another user).
        A claim becomes stale at 3:00 AM Moscow time each day.
        """
        return is_claim_stale(self.claimed_at)


class PlantListResponse(BaseModel):
    """Wrapped response for plant list with items key"""

    items: list[PlantListItem]
