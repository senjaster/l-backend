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


class WorkLogCreate(BaseModel):
    """Work log creation model"""
    
    id: Optional[UUID] = Field(default_factory=uuid4)
    started_at: datetime
    completed_at: Optional[datetime] = None
    installation_percentage: Optional[float] = Field(None, ge=0, le=100)
    inspector_id: int = Field(..., gt=0)
    plant_id: UUID


class WorkLogUpdate(BaseModel):
    """Work log update model"""
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    installation_percentage: Optional[float] = Field(None, ge=0, le=100)
    inspector_id: Optional[int] = None
    plant_id: Optional[UUID] = None


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


class WorkLogDetailResponse(BaseModel):
    """Detailed work log response with additional info"""
    
    id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    installation_percentage: Optional[float] = None
    inspector_id: int
    inspector_name: Optional[str] = None
    plant_id: UUID
    plant_name: Optional[str] = None
    is_deleted: bool
    server_modified_at: Optional[datetime] = None
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate duration in hours"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return round(delta.total_seconds() / 3600, 2)
        return None


class WorkLogStatistics(BaseModel):
    """Work log statistics"""
    
    total_work_logs: int
    active_work_logs: int
    completed_work_logs: int
    average_duration_hours: Optional[float] = None
    average_installation_percentage: Optional[float] = None
    total_by_plant: dict[UUID, int]
    total_by_inspector: dict[int, int]


class WorkLogInspector(BaseModel):
    """Work log - inspector relationship model"""
    
    work_log_id: UUID
    inspector_id: int
    inspector_name: Optional[str] = None


class WorkLogWithInspectors(BaseModel):
    """Work log with associated inspectors"""
    
    work_log: WorkLog
    inspectors: list[WorkLogInspector]


class WorkLogInspectorCreate(BaseModel):
    """Create relationship between work log and inspector"""
    
    work_log_id: UUID
    inspector_id: int


class WorkLogInspectorBulkCreate(BaseModel):
    """Bulk create relationships"""
    
    relationships: list[WorkLogInspectorCreate]