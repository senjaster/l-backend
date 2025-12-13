"""Image repository"""
from typing import Optional
from uuid import UUID
import json
import aiosql
from app.models.image import Image

# Load queries
queries = aiosql.from_path("app/queries/image", "asyncpg")


class ImageRepository:
    """Repository for Image aggregate"""
    
    async def get_by_id(self, conn, image_id: UUID) -> Optional[Image]:
        """Get image by ID"""
        row = await queries.get_by_id(conn, id=image_id)
        if row:
            # Parse JSONB metadata if it's a string
            row_dict = dict(row)
            if row_dict.get('metadata') and isinstance(row_dict['metadata'], str):
                row_dict['metadata'] = json.loads(row_dict['metadata'])
            return Image(**row_dict)
        return None
    
    async def save(self, conn, image: Image) -> Image:
        """Create or update image"""
        await queries.upsert(
            conn,
            id=image.id,
            equipment_id=image.equipment_id,
            original_file_name=image.original_file_name,
            image_type=image.image_type.value,
            metadata=json.dumps(image.metadata) if image.metadata else None
        )
        result = await self.get_by_id(conn, image.id)
        if not result:
            raise Exception("Failed to save image")
        return result
    
    async def delete(self, conn, image_id: UUID) -> bool:
        """Delete image (actual delete, no is_deleted flag)"""
        await queries.delete(conn, id=image_id)
        return True