"""EquipmentType aggregate models"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ControlPointTemplate(BaseModel):
    """Control point template for equipment type"""
    id: int
    equipment_type_id: int
    name: str
    short_name: str
    t_max: int
    t_excess: int
    default_sticker_id: Optional[int] = None


class EquipmentType(BaseModel):
    """EquipmentType aggregate with control point templates"""
    id: int
    name: str
    last_modified_at: datetime
    control_point_templates: list[ControlPointTemplate] = Field(default_factory=list)