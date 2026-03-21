"""Inspector model"""

from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel


class AccessLevel(str, Enum):
    """
    Access level for inspectors.
    
    - READ: Can only perform GET operations
    - INSPECT: Can perform GET operations and add inspections/defects
    - MODIFY: Can perform all operations including claiming plants and modifying equipment
    """
    READ = "READ"
    INSPECT = "INSPECT"
    MODIFY = "MODIFY"


class Inspector(BaseModel):
    """Inspector aggregate (read-only reference data)"""

    id: int
    full_name: str
    username: str
    access_level: AccessLevel = AccessLevel.READ
    is_deleted: bool = False
    server_modified_at: datetime


class InspectorListResponse(BaseModel):
    """List of Inspector items"""

    items: List[Inspector]
