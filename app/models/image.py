"""Image model"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ImageType(str, Enum):
    """Image type enum"""
    VISUAL = "VISUAL"
    THERMAL = "THERMAL"


class Image(BaseModel):
    """Image aggregate"""
    id: UUID
    equipment_id: UUID
    original_file_name: str
    image_type: ImageType
    metadata: Optional[dict] = None
    last_modified_at: datetime