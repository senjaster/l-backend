"""StickerType aggregate models"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StickerTempRange(BaseModel):
    """Temperature range for a sticker type"""
    id: int
    name: str
    t_min: int
    t_max: int


class StickerType(BaseModel):
    """StickerType aggregate with temperature ranges"""
    id: int
    name: str
    is_deleted: bool = False
    server_modified_at: datetime
    temp_ranges: list[StickerTempRange] = Field(default_factory=list)

class StickerTypeListResponse(BaseModel):
    """List of StickerType items"""
    items: List[StickerType]