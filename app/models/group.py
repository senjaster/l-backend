from __future__ import annotations
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.plant import Plant


# Read models (returned from GET endpoints)
class Group(BaseModel):
    """Hierarchical group - read model"""

    id: UUID
    name: str
    parent_group_id: Optional[UUID] = None
    is_deleted: bool = False
    server_modified_at: datetime
    children: List[Group] = Field(default_factory=list)
    plants: List[Plant] = Field(default_factory=list)

# List models
class GroupListItem(BaseModel):
    """Lightweight group item for list view"""

    id: UUID
    name: str
    parent_group_id: Optional[UUID] = None
    is_deleted: bool = False
    server_modified_at: datetime


class GroupListResponse(BaseModel):
    """Wrapped response for group list with items key"""

    items: List[GroupListItem]


# Request model for create/update
class GroupRequest(BaseModel):
    """Model for creating or updating a group"""

    name: str
    parent_group_id: Optional[UUID] = None


# Request model for adding plants to group
class AddPlantsToGroup(BaseModel):
    """Request model for adding plants to a group"""

    plant_ids: List[UUID]


# Path response
class GroupPathResponse(BaseModel):
    """Response containing the full path to a group"""

    items: List[GroupListItem]


# Tree response
class GroupTreeResponse(BaseModel):
    """Response containing the full group tree"""

    items: List[Group]