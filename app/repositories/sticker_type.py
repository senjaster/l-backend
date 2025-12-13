"""StickerType repository"""
from typing import Optional
import aiosql
from app.models.sticker_type import StickerType, StickerTempRange

# Load queries
queries = aiosql.from_path("app/queries/sticker_type", "asyncpg")


class StickerTypeRepository:
    """Repository for StickerType aggregate with child synchronization"""
    
    async def get_by_id(self, conn, sticker_type_id: int) -> Optional[StickerType]:
        """Get sticker type by ID with temperature ranges"""
        # Get sticker type
        sticker_row = await queries.get_by_id(conn, id=sticker_type_id)
        if not sticker_row:
            return None
        
        # Get temperature ranges
        temp_range_rows = [row async for row in queries.get_temp_ranges(conn, sticker_id=sticker_type_id)]
        temp_ranges = [StickerTempRange(**row) for row in temp_range_rows]
        
        return StickerType(**sticker_row, temp_ranges=temp_ranges)
    
    async def save(self, conn, sticker_type: StickerType) -> StickerType:
        """Save sticker type with child synchronization (must be called within transaction)"""
        # Upsert sticker type
        await queries.upsert_sticker_type(
            conn,
            id=sticker_type.id,
            name=sticker_type.name,
            is_deleted=sticker_type.is_deleted
        )
        
        # Synchronize temperature ranges
        await self._sync_temp_ranges(conn, sticker_type.id, sticker_type.temp_ranges)
        
        # Return updated aggregate
        return await self.get_by_id(conn, sticker_type.id)
    
    async def delete(self, conn, sticker_type_id: int) -> bool:
        """Logically delete sticker type (must be called within transaction)"""
        result = await queries.delete_sticker_type(conn, id=sticker_type_id)
        # aiosql returns status string like "UPDATE 1" for affected rows
        return result is not None and "0" not in result
    
    async def _sync_temp_ranges(self, conn, sticker_id: int, temp_ranges: list[StickerTempRange]):
        """Synchronize temperature ranges: match by ID, add new, delete removed"""
        # Get existing temp range IDs
        existing_rows = [row async for row in queries.get_temp_range_ids(conn, sticker_id=sticker_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {tr.id for tr in temp_ranges}
        
        # Update or insert
        for temp_range in temp_ranges:
            await queries.upsert_temp_range(
                conn,
                id=temp_range.id,
                sticker_id=sticker_id,
                name=temp_range.name,
                t_min=temp_range.t_min,
                t_max=temp_range.t_max
            )
        
        # Delete removed ranges
        to_delete = existing_ids - incoming_ids
        for temp_range_id in to_delete:
            await queries.delete_temp_range(conn, id=temp_range_id)