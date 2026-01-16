"""Inspector repository"""

from typing import Optional, List
from datetime import datetime, timezone
import aiosql
from app.config import settings
from app.utils.async_wrapper import AsyncWrapper
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.inspector import Inspector

# Load queries
_queries = aiosql.from_path("app/queries/inspector.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class InspectorRepository:
    """Repository for Inspector aggregate (read-only)"""

    async def get_all(
        self, conn, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> List[Inspector]:
        """Get all inspectors (without password_hash), optionally filtered by modification date"""
        inspectors = [
            row
            async for row in queries.get_all_inspectors(
                conn, modified_since=modified_since
            )
        ]
        return [Inspector(**row) for row in inspectors]

    async def get_by_id(self, conn, inspector_id: int) -> Optional[Inspector]:
        """Get inspector by ID"""
        row = await queries.get_by_id(conn, id=inspector_id)
        if row:
            return Inspector(**row)
        return None
