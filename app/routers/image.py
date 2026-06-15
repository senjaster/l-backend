"""Image router - implements API design principles"""

import asyncio
import logging

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request

from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.image import Image, PresignedUploadUrlResponse, ImageListResponse, ImageUploadStatus
from app.repositories.image import ConcurrentModificationError
from app.database import get_db_connection
from app.dependencies.permissions import get_permission_service
from app.services.permission_service import PermissionService
from app.services.s3_objects_service import S3ObjectService, get_s3_service

from app.models.inspector import AccessLevel
from app.utils.images_routines import image_repo, update_image_upload_status, fetch_images_background


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/image", tags=["image"])


@router.get("/all", response_model=ImageListResponse)
async def get_all_images(
    upload_status: Optional[str] = Query(
        None, description="Filter images by upload status"
    ),
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return images modified after this timestamp",
    ),
    uploaded_since: Optional[datetime] = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return images uploaded after this timestamp",
    ),
    conn=Depends(get_db_connection),
    limit: Optional[int] = Query(
        None, 
        description="Maximum number of images to return"
    )
) -> ImageListResponse:
    """Get all images (read-only), optionally filtered by modification date"""
    images = await image_repo.get_all(
        conn,
        upload_status=upload_status,
        modified_since=modified_since, 
        uploaded_since=uploaded_since, 
        limit=limit
    )
    return ImageListResponse(items=images)


@router.get("/by_id/{image_id}", response_model=Image)
async def get_image_by_id(
    image_id: UUID,
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_service)
) -> Image:
    """Get specific image by ID"""
    # Check plant access via image
    plant_id = await permission_service.get_plant_id_from_image(image_id)
    if not plant_id:
        raise HTTPException(status_code=404, detail="Image not found")
    await permission_service.require_plant_access(plant_id)
    
    image = await image_repo.get_by_id(conn, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Generate presigned URL for the image
    url_result = await s3_service.generate_presigned_url(image.id)
    if url_result:
        image.presigned_url, image.presigned_url_expires_at = url_result
    
    return image


@router.get("/by_plant_id/{plant_id}", response_model=list[Image])
async def get_images_by_plant_id(
    plant_id: UUID,
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return images modified after this timestamp",
    ),
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_service)
) -> list[Image]:
    """Get all images for a plant, optionally filtered by modification date"""
    # Check plant access
    await permission_service.require_plant_access(plant_id)
    
    images = await image_repo.get_by_plant_id(
        conn, plant_id, modified_since=modified_since
    )
    
    # Generate presigned URLs for all images
    for image in images:
        url_result = await s3_service.generate_presigned_url(image.id)
        if url_result:
            image.presigned_url, image.presigned_url_expires_at = url_result
    
    return images


@router.put("", response_model=Image)
async def upsert_image(
    image: Image,
    force: bool = Query(
        default=False, description="If true, ignore server_modified_at validation"
    ),
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_service)
) -> Image:
    """
    Create or replace image.

    Rules:
    - force=false (default):
      - Validates server_modified_at for existing images
      - Ignores server_modified_at for new images
    - force=true:
      - Ignores server_modified_at validation
    - Logical deletion via is_deleted flag (not implemented yet)
    - Permission: User must have access to the plant
    """
    try:
        async with conn.transaction():
            # Check access level (INSPECT required)
            permission_service.require_access_level(AccessLevel.INSPECT)
            
            # Check plant access
            await permission_service.require_plant_access(image.plant_id)
            
            result = await image_repo.save(conn, image, force=force)
        
        # Generate upload presigned URL
        url_result = await s3_service.generate_upload_presigned_url(result.id)
        if url_result:
            result.presigned_url, result.presigned_url_expires_at = url_result
        
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


@router.get("/{image_id}/upload_url", response_model=PresignedUploadUrlResponse)
async def get_upload_url(
    image_id: UUID,
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_service)
) -> PresignedUploadUrlResponse:
    """
    Get a presigned URL for uploading an image to S3.
    
    This endpoint generates a PUT presigned URL that allows clients to upload
    an image directly to S3. The URL is valid for a limited time as configured
    in the S3 service settings.
    
    Args:
        image_id: UUID of the image to upload
        
    Returns:
        PresignedUploadUrlResponse with the presigned URL and expiration time
        
    Raises:
        HTTPException: 500 if URL generation fails
        HTTPException: 403 if user lacks plant access
    """
    # Check plant access via image
    plant_id = await permission_service.get_plant_id_from_image(image_id)
    if not plant_id:
        raise HTTPException(status_code=404, detail="Image not found")
    await permission_service.require_plant_access(plant_id)
    
    url_result = await s3_service.generate_upload_presigned_url(image_id)
    if not url_result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate upload URL"
        )
    
    presigned_url, expires_at = url_result
    return PresignedUploadUrlResponse(
        presigned_url=presigned_url,
        presigned_url_expires_at=expires_at
    )


@router.get("/{image_id}/exists", response_model=dict)
async def check_image_exists(
    image_id: UUID,
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_service)
) -> dict[str, bool]:
    """
    Check if an image file exists in S3 storage.
    
    This endpoint issues a HEAD request to S3 to verify if the image file
    exists without downloading the actual file content.
    
    Args:
        image_id: UUID of the image to check
        
    Returns:
        Dictionary with 'exists' boolean field
        
    Raises:
        HTTPException: 403 if user lacks plant access
    """
    # Check plant access via image
    plant_id = await permission_service.get_plant_id_from_image(image_id)
    if not plant_id:
        raise HTTPException(status_code=404, detail="Image not found")
    await permission_service.require_plant_access(plant_id)
    
    exists = await s3_service.check_exists(image_id)
    return {"exists": exists}


@router.post("/trigger-images-background-fetch")
async def trigger_images_background_fetch(
    request: Request,
    upload_status: Optional[ImageUploadStatus] = None,
    modified_since: Optional[datetime] = datetime.now() - timedelta(days=2),
    uploaded_since: Optional[datetime] = datetime.now() - timedelta(days=30),
    batch_size: int = 500,
    timeout_seconds: int = 30,
    limit: Optional[int] = None
) -> dict[str, str]:
    """Запуск фоновой загрузки изображений"""
    base_url = f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"
    
    asyncio.create_task(
        fetch_images_background(
            base_url=base_url,
            upload_status=upload_status,
            modified_since=modified_since,
            uploaded_since=uploaded_since,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
            limit=limit
        )
    )
    
    return {
        "status": "Background upload has started",
        "base_url": base_url,
        "message": f"Images will be uploaded in batches with size of {batch_size}"
    }

