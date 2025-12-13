"""Equipment router"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from app.models.equipment import Equipment, EquipmentWrite
from app.repositories.equipment import EquipmentRepository
from app.database import get_db_connection

router = APIRouter(prefix="/equipment", tags=["equipment"])
equipment_repo = EquipmentRepository()


@router.get("/{equipment_id}", response_model=Equipment)
async def get_equipment(equipment_id: UUID, conn=Depends(get_db_connection)):
    """Get equipment with control points, defects, and inspection IDs"""
    equipment = await equipment_repo.get_by_id(conn, equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@router.put("/{equipment_id}", response_model=Equipment)
async def update_equipment(
    equipment_id: UUID,
    equipment: EquipmentWrite,
    conn=Depends(get_db_connection)
):
    """Create or update equipment with control points and defects"""
    try:
        async with conn.transaction():
            result = await equipment_repo.save(conn, equipment_id, equipment)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(equipment_id: UUID, conn=Depends(get_db_connection)):
    """Logically delete equipment"""
    async with conn.transaction():
        success = await equipment_repo.delete(conn, equipment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")