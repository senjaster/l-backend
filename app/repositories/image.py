"""Image repository"""
import json
import aiosql
import os
import logging

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from app.config import settings
from app.utils.async_wrapper import AsyncWrapper
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.image import Image
from app.models import ConflictError, ConflictDetail
from app.exceptions import ConcurrentModificationError
from app.utils.datetime_utils import truncate_to_milliseconds


# Load queries from single file
_queries = aiosql.from_path("app/queries/image.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries

logger = logging.getLogger(__name__)


class ImageRepository:
    """Repository for Image aggregate"""

    async def get_all(
        self, 
        conn, 
        modified_since: datetime = DEFAULT_MODIFIED_SINCE, 
        uploaded_since: Optional[datetime] = DEFAULT_MODIFIED_SINCE,
        limit: Optional[int] = None
    ) -> List[Image]:
        """Get all images, optionally filtered by modification date"""
        images = []
        async for row in queries.get_all_images(
                conn, 
                modified_since=modified_since, 
                uploaded_since=uploaded_since, 
                limit=limit
        ):
            # Convert the row to a dictionary and parse metadata if it's a string
            row_dict = dict(row)
            if 'metadata' in row_dict and isinstance(row_dict['metadata'], str):
                try:
                    row_dict['metadata'] = json.loads(row_dict['metadata'])
                except json.JSONDecodeError:
                    row_dict['metadata'] = {}
            
            images.append(Image(**row_dict))
        
        return images

    async def get_by_id(self, conn, image_id: UUID) -> Optional[Image]:
        """Get image by ID"""
        row = await queries.get_by_id(conn, id=image_id)
        if row:
            # Parse JSONB metadata if it's a string
            row_dict = dict(row)
            if row_dict.get("metadata") and isinstance(row_dict["metadata"], str):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            return Image(**row_dict)
        return None

    async def get_by_plant_id(
        self, conn, plant_id: UUID, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> list[Image]:
        """Get all images for a plant (joins through equipment and facility)"""
        rows = [
            row
            async for row in queries.get_by_plant_id(
                conn, plant_id=plant_id, modified_since=modified_since
            )
        ]
        images = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("metadata") and isinstance(row_dict["metadata"], str):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            images.append(Image(**row_dict))
        return images

    async def get_by_file_name(
        self, conn, file_name: str, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> list[Image]:
        """Get all images with a specific file name"""
        name, ext = os.path.splitext(file_name)
        rows = [row async for row in queries.get_by_file_name(
            conn, file_name=name, modified_since=modified_since
        )]
        images = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("metadata") and isinstance(row_dict["metadata"], str):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            images.append(Image(**row_dict))
        return images

    async def save(self, conn, image: Image, force: bool = False) -> Image:
        """
        Create or update image with optimistic concurrency control.
        Must be called within transaction.

        Args:
            conn: Database connection
            image: Image data to save
            force: If True, ignore server_modified_at validation

        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
            ValueError: If plant_id does not exist
        """
        image_id = image.id

        # Validate that plant_id exists
        result = await queries.plant_exists(conn, plant_id=image.plant_id)
        plant_exists = result["exists"] if result else False
        if not plant_exists:
            raise ValueError(f"Plant {image.plant_id} does not exist")

        # Get current state if exists
        current = await self.get_by_id(conn, image_id)

        # New server_modified_at timestamp
        new_server_modified_at = datetime.now(timezone.utc)

        if current and not (force or settings.disable_optimistic_locking):
            # Validate server_modified_at for existing image
            if image.server_modified_at is None:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="server_modified_at is required for updating existing image",
                        server_modified_at=current.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Missing server_modified_at in request",
                            )
                        ],
                    )
                )

            if truncate_to_milliseconds(
                image.server_modified_at
            ) != truncate_to_milliseconds(current.server_modified_at):
                raise ConcurrentModificationError(
                    ConflictError(
                        message="Image was modified by another client",
                        server_modified_at=current.server_modified_at,
                        client_modified_at=image.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Timestamp mismatch",
                                server_value=current.server_modified_at.isoformat(),
                                client_value=image.server_modified_at.isoformat(),
                            )
                        ],
                    )
                )

        # Upsert image
        await queries.upsert(
            conn,
            id=image_id,
            plant_id=image.plant_id,
            original_file_name=image.original_file_name,
            image_type=image.image_type.value,
            metadata=json.dumps(image.metadata) if image.metadata else None,
            is_deleted=image.is_deleted,
            server_modified_at=new_server_modified_at,
            upload_status=image.upload_status,
            server_uploaded_at=image.server_uploaded_at
        )

        result = await self.get_by_id(conn, image_id)
        if not result:
            raise ValueError(f"Image {image_id} not found after save")
        return result

    async def delete(self, conn, image_id: UUID) -> bool:
        """Delete image (actual delete, no is_deleted flag)"""
        await queries.delete(conn, id=image_id)
        return True

image_repo = ImageRepository()
