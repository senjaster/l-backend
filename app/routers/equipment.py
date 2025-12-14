"""Equipment router - implements new API design principles"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.equipment import Equipment, EquipmentListResponse
from app.repositories.equipment import EquipmentRepository, ConcurrentModificationError
from app.database import get_db_connection

router = APIRouter(prefix="/equipment", tags=["equipment"])
equipment_repo = EquipmentRepository()


@router.get("/all", response_model=EquipmentListResponse)
async def get_all_equipment(conn=Depends(get_db_connection)):
    """Get all equipment IDs (lightweight list) - for completeness"""
    return await equipment_repo.get_all(conn)


@router.get("/by_id/{equipment_id}", response_model=Equipment)
async def get_equipment_by_id(equipment_id: UUID, conn=Depends(get_db_connection)):
    """Get specific equipment with control points, defects, and inspection IDs"""
    equipment = await equipment_repo.get_by_id(conn, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.get("/by_plant_id/{plant_id}", response_model=EquipmentListResponse)
async def get_equipment_by_plant_id(plant_id: UUID, conn=Depends(get_db_connection)):
    """Get all equipment for a plant"""
    return await equipment_repo.get_by_plant_id(conn, plant_id)


@router.put("", response_model=Equipment)
async def upsert_equipment(
    equipment: Equipment,
    force: bool = Query(default=False, description="If true, ignore server_modified_at and mark extra children as deleted"),
    conn=Depends(get_db_connection)
):
    """
    Create or replace equipment with control points and defects.
    
    Rules:
    - force=false (default):
      - Validates server_modified_at for existing equipment
      - Rejects if extra child entities exist on server (409)
      - Ignores server_modified_at for new equipment
    - force=true:
      - Ignores server_modified_at validation
      - Marks extra child entities as deleted
    - Never allows "stealing" child entities from other equipment
    """
    try:
        async with conn.transaction():
            result = await equipment_repo.save(conn, equipment, force=force)
        return result
    except ConcurrentModificationError as e:
        raise HTTPException(
            status_code=409,
            detail=e.conflict_error.model_dump(mode='json')
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))