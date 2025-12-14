"""Equipment repository"""
from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
import aiosql
from app.models.equipment import (
    Equipment, ControlPoint, Defect,
    EquipmentListItem, EquipmentListResponse
)
from app.models import ConflictError, ConflictDetail

# Load queries from single file
queries = aiosql.from_path("app/queries/equipment.sql", "asyncpg")


class ConcurrentModificationError(Exception):
    """Raised when concurrent modification is detected"""
    def __init__(self, conflict_error: ConflictError):
        self.conflict_error = conflict_error
        super().__init__(conflict_error.message)


class EquipmentRepository:
    """Repository for Equipment aggregate with control point and defect synchronization and optimistic concurrency control"""
    
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
    
    async def get_all(self, conn) -> EquipmentListResponse:
        """Get all equipment as lightweight list"""
        equipment_rows = [row async for row in queries.get_all_equipment(conn)]
        equipment_list = [EquipmentListItem(**row) for row in equipment_rows]
        return EquipmentListResponse(items=equipment_list)
    
    async def get_by_plant_id(self, conn, plant_id: UUID) -> EquipmentListResponse:
        """Get all equipment for a plant"""
        equipment_rows = [row async for row in queries.get_by_plant_id(conn, plant_id=plant_id)]
        equipment_list = [EquipmentListItem(**row) for row in equipment_rows]
        return EquipmentListResponse(items=equipment_list)
    
    async def save(self, conn, equipment: Equipment, force: bool = False) -> Equipment:
        """
        Save equipment with control point and defect synchronization and optimistic concurrency control.
        Must be called within transaction.
        
        Args:
            conn: Database connection
            equipment_id: Equipment ID
            equipment: Equipment data to save
            force: If True, ignore server_modified_at and mark extra children as deleted
        
        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
        """
        equipment_id = equipment.id

        # Get current state if exists
        current = await self.get_by_id(conn, equipment_id)
        
        # New server_modified_at timestamp
        new_server_modified_at = datetime.now(timezone.utc)
        
        if current and not force:
            # Validate server_modified_at for existing equipment
            if equipment.server_modified_at is None:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="server_modified_at is required for updating existing equipment",
                        server_modified_at=current.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Missing server_modified_at in request"
                            )
                        ]
                    )
                )
            
            if equipment.server_modified_at != current.server_modified_at:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="Equipment was modified by another client",
                        server_modified_at=current.server_modified_at,
                        client_modified_at=equipment.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Timestamp mismatch",
                                server_value=current.server_modified_at.isoformat(),
                                client_value=equipment.server_modified_at.isoformat()
                            )
                        ]
                    )
                )
            
            # Check for extra control points on server
            current_cp_ids = {cp.id for cp in current.control_points if not cp.is_deleted}
            incoming_cp_ids = {cp.id for cp in equipment.control_points}
            extra_cp_ids = current_cp_ids - incoming_cp_ids
            
            # Check for extra defects on server
            current_defect_ids = {d.id for d in current.defects if not d.is_deleted}
            incoming_defect_ids = {d.id for d in equipment.defects}
            extra_defect_ids = current_defect_ids - incoming_defect_ids
            
            extra_child_ids = list(extra_cp_ids | extra_defect_ids)
            
            if extra_child_ids:
                conflicts = []
                if extra_cp_ids:
                    conflicts.append(
                        ConflictDetail(
                            field="control_points",
                            message=f"Server has {len(extra_cp_ids)} extra control points not in client request"
                        )
                    )
                if extra_defect_ids:
                    conflicts.append(
                        ConflictDetail(
                            field="defects",
                            message=f"Server has {len(extra_defect_ids)} extra defects not in client request"
                        )
                    )
                
                raise ConcurrentModificationError(
                    ConflictError(
                        message="Extra child entities exist on server",
                        server_modified_at=current.server_modified_at,
                        client_modified_at=equipment.server_modified_at,
                        extra_child_ids=extra_child_ids,
                        conflicts=conflicts
                    )
                )
        
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
            is_deleted=equipment.is_deleted,
            server_modified_at=new_server_modified_at
        )
        
        # Synchronize control points
        await self._sync_control_points(conn, equipment_id, equipment.control_points, force)
        
        # Synchronize defects
        await self._sync_defects(conn, equipment_id, equipment.defects, force)
        
        # Return updated aggregate
        result = await self.get_by_id(conn, equipment_id)
        if result is None:
            raise ValueError(f"Equipment {equipment_id} not found after save")
        return result
    
    async def delete(self, conn, equipment_id: UUID) -> bool:
        """Logically delete equipment (must be called within transaction)"""
        result = await queries.delete_equipment(conn, id=equipment_id)
        return result is not None and "0" not in result
    
    async def _sync_control_points(self, conn, equipment_id: UUID, control_points: Sequence[ControlPoint], force: bool):
        """
        Synchronize control points: match by ID, add new, mark removed as deleted.
        
        Args:
            conn: Database connection
            equipment_id: Equipment ID
            control_points: List of control points to sync
            force: If True, mark extra control points as deleted; if False, extras already validated
        """
        # Get existing control point IDs for this equipment
        existing_rows = [row async for row in queries.get_control_point_ids(conn, equipment_id=equipment_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {cp.id for cp in control_points}
        
        # Validate that control points being added/updated don't belong to another equipment (never allow stealing)
        for control_point in control_points:
            if control_point.id not in existing_ids:
                # This is a new control point or existing control point from another equipment
                # Check if it exists in another equipment
                existing_equipment_row = await queries.get_control_point_equipment_id(conn, control_point_id=control_point.id)
                if existing_equipment_row and existing_equipment_row['equipment_id'] != equipment_id:
                    raise ValueError(
                        f"Cannot transfer control point {control_point.id} from another equipment "
                        f"({existing_equipment_row['equipment_id']}). Child entities cannot be stolen."
                    )
        
        # Update or insert
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

        if force:
            # Mark removed control points as deleted (logical deletion)
            to_delete = existing_ids - incoming_ids
            for cp_id in to_delete:
                await queries.mark_control_point_deleted(conn, id=cp_id)
    
    async def _sync_defects(self, conn, equipment_id: UUID, defects: Sequence[Defect], force: bool):
        """
        Synchronize defects: match by ID, add new, mark removed as deleted.
        
        Args:
            conn: Database connection
            equipment_id: Equipment ID
            defects: List of defects to sync
            force: If True, mark extra defects as deleted; if False, extras already validated
        """
        # Get existing defect IDs for this equipment
        existing_rows = [row async for row in queries.get_defect_ids(conn, equipment_id=equipment_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {d.id for d in defects}
        
        # Validate that defects being added/updated don't belong to another equipment (never allow stealing)
        for defect in defects:
            if defect.id not in existing_ids:
                # This is a new defect or existing defect from another equipment
                # Check if it exists in another equipment
                existing_equipment_row = await queries.get_defect_equipment_id(conn, defect_id=defect.id)
                if existing_equipment_row and existing_equipment_row['equipment_id'] != equipment_id:
                    raise ValueError(
                        f"Cannot transfer defect {defect.id} from another equipment "
                        f"({existing_equipment_row['equipment_id']}). Child entities cannot be stolen."
                    )
        
        # Update or insert (is_deleted is always False for incoming defects)
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

        if force:   
            # Mark removed defects as deleted (logical deletion)
            to_delete = existing_ids - incoming_ids
            for defect_id in to_delete:
                await queries.mark_defect_deleted(conn, id=defect_id)