"""Equipment aggregate models"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class DefectStatus(str, Enum):
    """Defect status enum"""
    DETECTED = "DETECTED"
    RESOLVED = "RESOLVED"


class ControlPoint(BaseModel):
    """Control point within equipment (child entity)"""
    id: UUID
    control_point_type: str
    point_count: int
    sticker_count: int
    sticker_type_id: Optional[int] = None
    t_max: int
    t_excess: int
    is_deleted: bool = False


class Defect(BaseModel):
    """Defect within equipment (child entity)"""
    id: UUID
    unit_name: str
    t_max: Optional[int] = None
    t_excess: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: DefectStatus = DefectStatus.DETECTED
    is_deleted: bool = False


class Equipment(BaseModel):
    """Equipment aggregate root - read model"""
    id: UUID
    plant_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    is_container: bool = False
    equipment_type_id: Optional[int] = None
    estimated_point_count: Optional[int] = None
    is_deleted: bool = False
    server_modified_at: datetime
    control_points: list[ControlPoint] = Field(default_factory=list)
    defects: list[Defect] = Field(default_factory=list)
    inspection_ids: Optional[list[UUID]] = Field(default_factory=list)

# List models
class EquipmentListItem(BaseModel):
    """Lightweight equipment item for list view"""
    id: UUID
    plant_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    is_container: bool
    equipment_type_id: Optional[int] = None
    is_deleted: bool


class EquipmentListResponse(BaseModel):
    """Wrapped response for equipment list with items key"""
    items: list[EquipmentListItem]


# Conflict error models
class ConflictDetail(BaseModel):
    """Details about a specific conflict"""
    field: str
    message: str
    server_value: Optional[str] = None
    client_value: Optional[str] = None


class ConflictError(BaseModel):
    """Conflict error response (409)"""
    error: str = "conflict"
    message: str
    server_modified_at: datetime
    client_modified_at: Optional[datetime] = None
    conflicts: list[ConflictDetail] = Field(default_factory=list)
    extra_child_ids: list[UUID] = Field(default_factory=list)