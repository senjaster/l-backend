"""StickerType router"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.sticker_type import StickerTypeListResponse
from app.repositories.sticker_type import StickerTypeRepository
from app.database import get_db_connection

router = APIRouter(prefix="/sticker-type", tags=["sticker-type"])
sticker_type_repo = StickerTypeRepository()


@router.get("/all", response_model=StickerTypeListResponse)
async def get_all_sticker_types(conn=Depends(get_db_connection)):
    """Get all sticker types with temperature ranges"""
    sticker_types = await sticker_type_repo.get_all(conn)
    return StickerTypeListResponse(items=sticker_types)