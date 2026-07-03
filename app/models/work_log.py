"""Work log aggregate models"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


class WorkLog(BaseModel):
    """Work log aggregate root - read model"""
    
    id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    installation_percentage: Optional[float] = Field(None, ge=0, le=100)
    inspector_id: int
    plant_id: UUID
    is_deleted: bool = False
    server_modified_at: Optional[datetime] = None
    duration_hours: Optional[float] = None


class WorkLogListItem(BaseModel):
    """Lightweight work log item for list view"""
    
    id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    installation_percentage: Optional[float] = None
    inspector_id: int
    plant_id: UUID
    is_deleted: bool


class WorkLogListResponse(BaseModel):
    """Wrapped response for work log list with items key"""
    
    items: list[WorkLogListItem]
    total: Optional[int] = None
    skip: Optional[int] = None
    limit: Optional[int] = None


class WorkLogInspector(BaseModel):
    """Work log - inspector relationship model"""
    
    work_log_id: UUID
    inspector_id: int
    inspector_name: Optional[str] = None

