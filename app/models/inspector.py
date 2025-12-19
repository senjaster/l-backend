"""Inspector model"""
from datetime import datetime
from typing import List
from pydantic import BaseModel


class Inspector(BaseModel):
    """Inspector aggregate (read-only reference data)"""
    id: int
    full_name: str
    username: str
    is_deleted: bool = False
    server_modified_at: datetime


class InspectorListResponse(BaseModel):
    """List of Inspector items"""
    items: List[Inspector]