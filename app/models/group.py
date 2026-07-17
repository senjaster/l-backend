from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class Group(BaseModel):
    """Hierarchical group"""

    id: UUID
    name: str
    parent_group_id: Optional[UUID] = None
    is_deleted: bool = False
    server_modified_at: datetime


class GroupListResponse(BaseModel):
    """Wrapped response for group list with items key"""

    items: List[Group]
