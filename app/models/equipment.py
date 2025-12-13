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


class ControlPointWrite(BaseModel):
    """Control point for write operations"""
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


class DefectWrite(BaseModel):
    """Defect for write operations"""
    id: UUID
    unit_name: str
    t_max: Optional[int] = None
    t_excess: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: DefectStatus = DefectStatus.DETECTED
    is_deleted: bool = False


class Equipment(BaseModel):
    """Equipment aggregate root"""
    id: UUID
    plant_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    is_container: bool = False
    equipment_type_id: Optional[int] = None
    estimated_point_count: Optional[int] = None
    is_deleted: bool = False
    last_modified_at: datetime
    control_points: list[ControlPoint] = Field(default_factory=list)
    defects: list[Defect] = Field(default_factory=list)
    inspection_ids: list[UUID] = Field(default_factory=list)


class EquipmentWrite(BaseModel):
    """Equipment for write operations (no id, no is_deleted, no timestamps, no inspection_ids)"""
    plant_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    is_container: bool = False
    equipment_type_id: Optional[int] = None
    estimated_point_count: Optional[int] = None
    control_points: list[ControlPointWrite] = Field(default_factory=list)
    defects: list[DefectWrite] = Field(default_factory=list)