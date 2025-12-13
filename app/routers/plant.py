"""Plant router"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models.plant import Plant, PlantWrite, PlantListResponse
from app.repositories.plant import PlantRepository
from app.database import get_db_connection

router = APIRouter(prefix="/plant", tags=["plant"])
plant_repo = PlantRepository()


class LockRequest(BaseModel):
    """Request to lock a plant"""
    device_id: UUID
    user_id: int


@router.get("/plants", response_model=PlantListResponse)
async def get_all_plants(conn=Depends(get_db_connection)):
    """Get all plants as lightweight list"""
    return await plant_repo.get_all(conn)


@router.get("/{plant_id}", response_model=Plant)
async def get_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Get plant with facilities and equipment IDs"""
    plant = await plant_repo.get_by_id(conn, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("/{plant_id}", response_model=Plant)
async def update_plant(
    plant_id: UUID,
    plant: PlantWrite,
    conn=Depends(get_db_connection)
):
    """Create or update plant with facilities"""
    try:
        async with conn.transaction():
            result = await plant_repo.save(conn, plant_id, plant)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{plant_id}", status_code=204)
async def delete_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Logically delete plant"""
    async with conn.transaction():
        success = await plant_repo.delete(conn, plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")


@router.post("/{plant_id}/lock", status_code=204)
async def lock_plant(
    plant_id: UUID,
    lock_request: LockRequest,
    conn=Depends(get_db_connection)
):
    """Lock plant for editing"""
    async with conn.transaction():
        success = await plant_repo.lock(
            conn,
            plant_id,
            lock_request.device_id,
            lock_request.user_id
        )
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")


@router.post("/{plant_id}/unlock", status_code=204)
async def unlock_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Unlock plant"""
    async with conn.transaction():
        success = await plant_repo.unlock(conn, plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")