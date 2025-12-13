"""Inspector model"""
from datetime import datetime
from pydantic import BaseModel


class Inspector(BaseModel):
    """Inspector aggregate (read-only reference data)"""
    id: int
    full_name: str
    username: str
    password_hash: str
    server_modified_at: datetime