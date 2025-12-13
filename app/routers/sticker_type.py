"""StickerType router"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.sticker_type import StickerType
from app.repositories.sticker_type import StickerTypeRepository
from app.database import get_db_connection

router = APIRouter(prefix="/sticker-type", tags=["sticker-type"])
sticker_type_repo = StickerTypeRepository()


@router.get("/{sticker_type_id}", response_model=StickerType)
async def get_sticker_type(sticker_type_id: int, conn=Depends(get_db_connection)):
    """Get sticker type with temperature ranges"""
    sticker_type = await sticker_type_repo.get_by_id(conn, sticker_type_id)
    if not sticker_type:
        raise HTTPException(status_code=404, detail="Sticker type not found")
    return sticker_type


@router.put("/{sticker_type_id}", response_model=StickerType)
async def update_sticker_type(
    sticker_type_id: int,
    sticker_type: StickerType,
    conn=Depends(get_db_connection)
):
    """Create or update sticker type with temperature ranges"""
    if sticker_type.id != sticker_type_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    
    async with conn.transaction():
        result = await sticker_type_repo.save(conn, sticker_type)
    return result


@router.delete("/{sticker_type_id}", status_code=204)
async def delete_sticker_type(sticker_type_id: int, conn=Depends(get_db_connection)):
    """Logically delete sticker type"""
    async with conn.transaction():
        success = await sticker_type_repo.delete(conn, sticker_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sticker type not found")