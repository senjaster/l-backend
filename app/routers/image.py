"""Image router - implements API design principles"""

from uuid import UUID
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.image import Image
from app.repositories.image import ImageRepository, ConcurrentModificationError
from app.database import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/image", tags=["image"])
image_repo = ImageRepository()


@router.get("/by_id/{image_id}", response_model=Image)
async def get_image_by_id(image_id: UUID, conn=Depends(get_db_connection)):
    """Get specific image by ID"""
    image = await image_repo.get_by_id(conn, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.get("/by_plant_id/{plant_id}", response_model=list[Image])
async def get_images_by_plant_id(
    plant_id: UUID,
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return images modified after this timestamp",
    ),
    conn=Depends(get_db_connection),
):
    """Get all images for a plant, optionally filtered by modification date"""
    return await image_repo.get_by_plant_id(
        conn, plant_id, modified_since=modified_since
    )


@router.put("", response_model=Image)
async def upsert_image(
    image: Image,
    force: bool = Query(
        default=False, description="If true, ignore server_modified_at validation"
    ),
    conn=Depends(get_db_connection),
):
    """
    Create or replace image.

    Rules:
    - force=false (default):
      - Validates server_modified_at for existing images
      - Ignores server_modified_at for new images
    - force=true:
      - Ignores server_modified_at validation
    - Logical deletion via is_deleted flag (not implemented yet)
    """
    try:
        async with conn.transaction():
            result = await image_repo.save(conn, image, force=force)
        return result
    except ConcurrentModificationError as e:
        logger.warning(
            "Concurrent modification detected for image",
            extra={
                "image_id": str(image.id),
                "conflict": e.conflict_error.model_dump(mode="json"),
            },
        )
        raise HTTPException(
            status_code=409, detail=e.conflict_error.model_dump(mode="json")
        )
    except ValueError as e:
        logger.warning(
            "Invalid image data", extra={"image_id": str(image.id), "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))
