"""Plant router - implements new API design principles"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.models.plant import Plant, PlantListResponse
from app.repositories.plant import PlantRepository, ConcurrentModificationError
from app.database import get_db_connection

router = APIRouter(prefix="/plant", tags=["plant"])
plant_repo = PlantRepository()


class LockRequest(BaseModel):
    """Request to lock a plant"""
    device_id: UUID
    user_id: int


@router.get("/all", response_model=PlantListResponse)
async def get_all_plants(conn=Depends(get_db_connection)):
    """Get all plant IDs (lightweight list) - for completeness"""
    return await plant_repo.get_all(conn)


@router.get("/by_id/{plant_id}", response_model=Plant)
async def get_plant_by_id(plant_id: UUID, conn=Depends(get_db_connection)):
    """Get specific plant with facilities and equipment IDs"""
    plant = await plant_repo.get_by_id(conn, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("", response_model=Plant)
async def upsert_plant(
    plant: Plant,
    force: bool = Query(default=False, description="If true, ignore server_modified_at and mark extra children as deleted"),
    conn=Depends(get_db_connection)
):
    """
    Create or replace plant with facilities.
    
    Rules:
    - force=false (default):
      - Validates server_modified_at for existing plants
      - Rejects if extra child facilities exist on server (409)
      - Ignores server_modified_at for new plants
    - force=true:
      - Ignores server_modified_at validation
      - Marks extra child facilities as deleted
    - Never allows "stealing" facilities from other plants
    """
    try:
        async with conn.transaction():
            result = await plant_repo.save(conn, plant, force=force)
        return result
    except ConcurrentModificationError as e:
        raise HTTPException(
            status_code=409,
            detail=e.conflict_error.model_dump(mode='json')
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/by_id/{plant_id}/lock", status_code=204)
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


@router.post("/by_id/{plant_id}/unlock", status_code=204)
async def unlock_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Unlock plant"""
    async with conn.transaction():
        success = await plant_repo.unlock(conn, plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")