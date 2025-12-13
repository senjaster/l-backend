"""EquipmentType repository"""
from typing import Optional
import aiosql
from app.models.equipment_type import EquipmentType, ControlPointTemplate

# Load queries
queries = aiosql.from_path("app/queries/equipment_type", "asyncpg")


class EquipmentTypeRepository:
    """Repository for EquipmentType aggregate with child synchronization"""
    
    async def get_by_id(self, conn, equipment_type_id: int) -> Optional[EquipmentType]:
        """Get equipment type by ID with control point templates"""
        # Get equipment type
        equipment_type_row = await queries.get_by_id(conn, id=equipment_type_id)
        if not equipment_type_row:
            return None
        
        # Get control point templates
        template_rows = await queries.get_control_point_templates(
            conn, 
            equipment_type_id=equipment_type_id
        )
        templates = [ControlPointTemplate(**row) for row in template_rows]
        
        return EquipmentType(**equipment_type_row, control_point_templates=templates)
    
    async def save(self, conn, equipment_type: EquipmentType) -> EquipmentType:
        """Save equipment type with child synchronization (must be called within transaction)"""
        # Upsert equipment type
        await queries.upsert_equipment_type(
            conn,
            id=equipment_type.id,
            name=equipment_type.name
        )
        
        # Synchronize control point templates
        await self._sync_templates(
            conn, 
            equipment_type.id, 
            equipment_type.control_point_templates
        )
        
        # Return updated aggregate
        return await self.get_by_id(conn, equipment_type.id)
    
    async def delete(self, conn, equipment_type_id: int) -> bool:
        """Delete equipment type (must be called within transaction)"""
        result = await queries.delete_equipment_type(conn, id=equipment_type_id)
        return result > 0
    
    async def _sync_templates(
        self, 
        conn, 
        equipment_type_id: int, 
        templates: list[ControlPointTemplate]
    ):
        """Synchronize control point templates: match by ID, add new, delete removed"""
        # Get existing template IDs
        existing_rows = await queries.get_template_ids(conn, equipment_type_id=equipment_type_id)
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {t.id for t in templates}
        
        # Update or insert
        for template in templates:
            await queries.upsert_template(
                conn,
                id=template.id,
                equipment_type_id=equipment_type_id,
                name=template.name,
                short_name=template.short_name,
                t_max=template.t_max,
                t_excess=template.t_excess,
                default_sticker_id=template.default_sticker_id
            )
        
        # Delete removed templates
        to_delete = existing_ids - incoming_ids
        for template_id in to_delete:
            await queries.delete_template(conn, id=template_id)