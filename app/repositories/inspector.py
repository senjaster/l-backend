"""Inspector repository"""
from typing import Optional
import aiosql
from app.models.inspector import Inspector

# Load queries
queries = aiosql.from_path("app/queries/inspector", "asyncpg")


class InspectorRepository:
    """Repository for Inspector aggregate (read-only)"""
    
    async def get_by_id(self, conn, inspector_id: int) -> Optional[Inspector]:
        """Get inspector by ID"""
        row = await queries.get_by_id(conn, id=inspector_id)
        if row:
            return Inspector(**row)
        return None