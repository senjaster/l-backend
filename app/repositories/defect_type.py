"""DefectType repository"""

from typing import List
from datetime import datetime
import aiosql
from aiosql.queries import Queries
from app.config import settings
from app.utils.async_wrapper import AsyncWrapper
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.defect_type import DefectType

# Load queries
_queries = aiosql.from_path("app/queries/defect_type.sql", settings.db_driver)
queries: Queries = (
    AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries
)  # type: ignore[assignment]


class DefectTypeRepository:
    """Repository for DefectType aggregate"""

    async def get_all(
        self, conn, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> List[DefectType]:
        """Get all defect types, optionally filtered by modification date"""
        defect_types = [
            DefectType(**row)
            async for row in queries.get_all_defect_types(
                conn, modified_since=modified_since
            )
        ]
        return defect_types
