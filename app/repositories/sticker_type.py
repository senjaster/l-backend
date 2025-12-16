"""StickerType repository"""
from typing import List
import aiosql
from app.models.sticker_type import StickerType, StickerTempRange
from itertools import groupby

# Load queries
queries = aiosql.from_path("app/queries/sticker_type.sql", "asyncpg")


class StickerTypeRepository:
    """Repository for StickerType aggregate with child synchronization"""

    async def get_all(self, conn) -> List[StickerType]:
        """Get all sticker types with temperature ranges"""
        # Get sticker types
        sticker_types = [row async for row in queries.get_sticker_types(conn)]
        if not sticker_types:
            return []
        temp_ranges_raw: list[dict] = [row async for row in queries.get_temp_ranges(conn)]
        temp_ranges = {
            key: [StickerTempRange(**row) for row in value] 
            for key, value 
            in groupby(temp_ranges_raw, lambda r: r["sticker_id"])
        }
        return [
            StickerType(
                **row,
                temp_ranges=temp_ranges.get(row["id"], [])
            )
            for row
            in sticker_types
        ]
        