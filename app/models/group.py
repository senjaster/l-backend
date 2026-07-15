from __future__ import annotations
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.plant import Plant


class Group(BaseModel):
    """Hierarchical group - read model"""

    id: UUID
    name: str
    parent_group_id: Optional[UUID] = None
    is_deleted: bool = False
    server_modified_at: datetime
    children: List[Group] = Field(default_factory=list)

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
