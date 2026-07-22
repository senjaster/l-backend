from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PlantGroup(BaseModel):
    """Hierarchical group"""

    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    is_deleted: bool = False
    server_modified_at: datetime


class PlantGroupListResponse(BaseModel):
    """Wrapped response for group list with items key"""

    items: List[PlantGroup]
