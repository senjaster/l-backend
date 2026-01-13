"""Plant aggregate models"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models import ConflictDetail, ConflictError


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
    grabbed_by_device_id: Optional[UUID] = None
    grabbed_by_user_id: Optional[int] = None
    grabbed_at: Optional[datetime] = None
    is_deleted: bool = False
    server_modified_at: datetime
    facilities: list[Facility] = Field(default_factory=list)


# List models
class PlantListItem(BaseModel):
    """Lightweight plant item for list view"""
    id: UUID
    name: str
    grabbed_by_device_id: Optional[UUID] = None
    grabbed_by_user_id: Optional[int] = None
    grabbed_at: Optional[datetime] = None
    is_deleted: bool = False
    server_modified_at: datetime


class PlantListResponse(BaseModel):
    """Wrapped response for plant list with items key"""
    items: list[PlantListItem]

