"""Equipment repository"""
from typing import Optional, Union, Sequence
from uuid import UUID
from datetime import datetime, timezone
import aiosql
from app.models.equipment import (
    Equipment, ControlPoint, Defect,
    EquipmentWrite, ControlPointWrite, DefectWrite
)

# Load queries from single file
queries = aiosql.from_path("app/queries/equipment.sql", "asyncpg")


class EquipmentRepository:
    """Repository for Equipment aggregate with control point and defect synchronization"""
    
    async def get_by_id(self, conn, equipment_id: UUID) -> Optional[Equipment]:
        """Get equipment by ID with control points, defects, and inspection IDs"""
        # Get equipment
        equipment_row = await queries.get_by_id(conn, id=equipment_id)
        if not equipment_row:
            return None
        
        # Get control points (exclude equipment_id from row data)
        control_point_rows = [row async for row in queries.get_control_points(conn, equipment_id=equipment_id)]
        control_points = [
            ControlPoint(**{k: v for k, v in row.items() if k != 'equipment_id'})
            for row in control_point_rows
        ]
        
        # Get defects (exclude equipment_id from row data)
        defect_rows = [row async for row in queries.get_defects(conn, equipment_id=equipment_id)]
        defects = [
            Defect(**{k: v for k, v in row.items() if k != 'equipment_id'})
            for row in defect_rows
        ]
        
        # Get inspection IDs
        inspection_rows = [row async for row in queries.get_inspection_ids(conn, equipment_id=equipment_id)]
        inspection_ids = [row['id'] for row in inspection_rows]
        
        return Equipment(
            **equipment_row,
            control_points=control_points,
            defects=defects,
            inspection_ids=inspection_ids
        )
    
    async def save(self, conn, equipment_id: UUID, equipment: Union[Equipment, EquipmentWrite]) -> Equipment:
        """Save equipment with control point and defect synchronization (must be called within transaction)"""
        # Determine is_deleted value (EquipmentWrite doesn't have it, so default to False)
        is_deleted = equipment.is_deleted if isinstance(equipment, Equipment) else False
        
        # Determine last_modified_at (EquipmentWrite doesn't have it, so use current time)
        last_modified_at = equipment.last_modified_at if isinstance(equipment, Equipment) else datetime.now(timezone.utc)
        
        # Upsert equipment
        await queries.upsert_equipment(
            conn,
            id=equipment_id,
            plant_id=equipment.plant_id,
            parent_id=equipment.parent_id,
            name=equipment.name,
            is_container=equipment.is_container,
            equipment_type_id=equipment.equipment_type_id,
            estimated_point_count=equipment.estimated_point_count,
            is_deleted=is_deleted,
            last_modified_at=last_modified_at
        )
        
        # Synchronize control points
        await self._sync_control_points(conn, equipment_id, equipment.control_points)
        
        # Synchronize defects
        await self._sync_defects(conn, equipment_id, equipment.defects)
        
        # Return updated aggregate
        return await self.get_by_id(conn, equipment_id)
    
    async def delete(self, conn, equipment_id: UUID) -> bool:
        """Logically delete equipment (must be called within transaction)"""
        result = await queries.delete_equipment(conn, id=equipment_id)
        return result is not None and "0" not in result
    
    async def _sync_control_points(self, conn, equipment_id: UUID, control_points: Sequence[Union[ControlPoint, ControlPointWrite]]):
        """Synchronize control points: match by control_point_type, upsert incoming ones"""
        # Update or insert incoming control points with their is_deleted status
        for control_point in control_points:
            await queries.upsert_control_point(
                conn,
                id=control_point.id,
                equipment_id=equipment_id,
                control_point_type=control_point.control_point_type,
                point_count=control_point.point_count,
                sticker_count=control_point.sticker_count,
                sticker_type_id=control_point.sticker_type_id,
                t_max=control_point.t_max,
                t_excess=control_point.t_excess,
                is_deleted=control_point.is_deleted
            )
    
    async def _sync_defects(self, conn, equipment_id: UUID, defects: Sequence[Union[Defect, DefectWrite]]):
        """Synchronize defects: match by ID, validate ownership, upsert incoming ones"""
        # Get existing defect IDs for this equipment
        existing_rows = [row async for row in queries.get_defect_ids(conn, equipment_id=equipment_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        # Validate that defects being added/updated don't belong to another equipment
        for defect in defects:
            if defect.id not in existing_ids:
                # This is a new defect or existing defect from another equipment
                # Check if it exists in another equipment
                existing_equipment_row = await queries.get_defect_equipment_id(conn, defect_id=defect.id)
                if existing_equipment_row and existing_equipment_row['equipment_id'] != equipment_id:
                    raise ValueError(
                        f"Defect {defect.id} belongs to another equipment "
                        f"({existing_equipment_row['equipment_id']}) and cannot be transferred"
                    )
        
        # Update or insert incoming defects with their is_deleted status
        for defect in defects:
            await queries.upsert_defect(
                conn,
                id=defect.id,
                equipment_id=equipment_id,
                unit_name=defect.unit_name,
                t_max=defect.t_max,
                t_excess=defect.t_excess,
                detected_at=defect.detected_at,
                resolved_at=defect.resolved_at,
                status=defect.status.value,
                is_deleted=defect.is_deleted
            )