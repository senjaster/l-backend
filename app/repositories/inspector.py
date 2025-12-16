"""Inspector repository"""
from typing import Optional, List
import aiosql
from app.models.inspector import Inspector

# Load queries
queries = aiosql.from_path("app/queries/inspector.sql", "asyncpg")


class InspectorRepository:
    """Repository for Inspector aggregate (read-only)"""
    
    async def get_all(self, conn) -> List[Inspector]:
        """Get all inspectors (without password_hash)"""
        inspectors = [row async for row in queries.get_all_inspectors(conn)]
        return [Inspector(**row) for row in inspectors]
    
    async def get_by_id(self, conn, inspector_id: int) -> Optional[Inspector]:
        """Get inspector by ID"""
        row = await queries.get_by_id(conn, id=inspector_id)
        if row:
            return Inspector(**row)
        return None