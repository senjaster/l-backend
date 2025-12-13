"""EquipmentType router"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.equipment_type import EquipmentType
from app.repositories.equipment_type import EquipmentTypeRepository
from app.database import get_db_connection

router = APIRouter(prefix="/equipment-type", tags=["equipment-type"])
equipment_type_repo = EquipmentTypeRepository()


@router.get("/{equipment_type_id}", response_model=EquipmentType)
async def get_equipment_type(equipment_type_id: int, conn=Depends(get_db_connection)):
    """Get equipment type with control point templates"""
    equipment_type = await equipment_type_repo.get_by_id(conn, equipment_type_id)
    if not equipment_type:
        raise HTTPException(status_code=404, detail="Equipment type not found")
    return equipment_type


@router.put("/{equipment_type_id}", response_model=EquipmentType)
async def update_equipment_type(
    equipment_type_id: int,
    equipment_type: EquipmentType,
    conn=Depends(get_db_connection)
):
    """Create or update equipment type with control point templates"""
    if equipment_type.id != equipment_type_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    
    async with conn.transaction():
        result = await equipment_type_repo.save(conn, equipment_type)
    return result


@router.delete("/{equipment_type_id}", status_code=204)
async def delete_equipment_type(equipment_type_id: int, conn=Depends(get_db_connection)):
    """Delete equipment type"""
    async with conn.transaction():
        success = await equipment_type_repo.delete(conn, equipment_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment type not found")