"""Image router"""
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from app.models.image import Image
from app.repositories.image import ImageRepository
from app.database import get_db_connection

router = APIRouter(prefix="/image", tags=["image"])
image_repo = ImageRepository()


@router.get("/{image_id}", response_model=Image)
async def get_image(image_id: UUID, conn=Depends(get_db_connection)):
    """Get image by ID"""
    image = await image_repo.get_by_id(conn, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.put("/{image_id}", response_model=Image)
async def update_image(image_id: UUID, image: Image, conn=Depends(get_db_connection)):
    """Create or update image"""
    if image.id != image_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    
    async with conn.transaction():
        result = await image_repo.save(conn, image)
    return result


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: UUID, conn=Depends(get_db_connection)):
    """Delete image (actual delete)"""
    async with conn.transaction():
        success = await image_repo.delete(conn, image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")