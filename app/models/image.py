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


class PresignedUploadUrlResponse(BaseModel):
    """Response model for presigned upload URL"""
    presigned_url: str
    presigned_url_expires_at: datetime


class Image(BaseModel):
    """Image aggregate"""

    id: UUID
    plant_id: UUID
    original_file_name: str
    image_type: ImageType
    metadata: Optional[dict] = None
    is_deleted: bool = False
    server_modified_at: datetime
    presigned_url: Optional[str] = None  # Generated dynamically, not stored in DB
    presigned_url_expires_at: Optional[datetime] = None  # Expiration time for presigned URL
