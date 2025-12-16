"""EquipmentType router"""
from fastapi import APIRouter, Depends
from app.models.equipment_type import EquipmentTypeListResponse
from app.repositories.equipment_type import EquipmentTypeRepository
from app.database import get_db_connection

router = APIRouter(prefix="/equipment-type", tags=["equipment-type"])
equipment_type_repo = EquipmentTypeRepository()


@router.get("/all", response_model=EquipmentTypeListResponse)
async def get_all_equipment_types(conn=Depends(get_db_connection)):
    """Get all equipment types with control point templates"""
    equipment_types = await equipment_type_repo.get_all(conn)
    return EquipmentTypeListResponse(items=equipment_types)