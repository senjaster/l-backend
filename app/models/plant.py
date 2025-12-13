"""Plant aggregate models"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# Read models (returned from GET endpoints)
class Facility(BaseModel):
    """Energy facility (part of plant) - read model"""
    id: UUID
    name: str
    is_deleted: bool = False
    equipment_ids: list[UUID] = Field(default_factory=list)


class Plant(BaseModel):
    """Plant aggregate with facilities - read model"""
    id: UUID
    name: str
    locked_by_device_id: Optional[UUID] = None
    locked_by_user_id: Optional[int] = None
    locked_at: Optional[datetime] = None
    is_deleted: bool = False
    last_modified_at: datetime
    facilities: list[Facility] = Field(default_factory=list)


# Write models (used in PUT requests)
class FacilityWrite(BaseModel):
    """Energy facility write model - for creating/updating facilities"""
    id: UUID
    name: str


class PlantWrite(BaseModel):
    """Plant write model - for creating/updating plants"""
    name: str
    locked_by_device_id: Optional[UUID] = None
    locked_by_user_id: Optional[int] = None
    locked_at: Optional[datetime] = None
    last_modified_at: datetime
    facilities: list[FacilityWrite] = Field(default_factory=list)


# List models
class PlantListItem(BaseModel):
    """Lightweight plant item for list view"""
    id: UUID
    name: str
    is_deleted: bool
    locked_by_device_id: Optional[UUID] = None
    locked_by_user_id: Optional[int] = None
    locked_at: Optional[datetime] = None


class PlantListResponse(BaseModel):
    """Wrapped response for plant list"""
    plants: list[PlantListItem]