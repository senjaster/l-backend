"""Plant repository"""
from typing import Optional, Union
from uuid import UUID
from datetime import datetime, timezone
import aiosql
from app.models.plant import (
    Plant, Facility,
    PlantListItem, PlantListResponse
)
from app.models import ConflictError, ConflictDetail
from app.exceptions import ConcurrentModificationError

# Load queries from single file
queries = aiosql.from_path("app/queries/plant.sql", "asyncpg")


class PlantRepository:
    """Repository for Plant aggregate with facility synchronization and optimistic concurrency control"""
    
    async def get_by_id(self, conn, plant_id: UUID) -> Optional[Plant]:
        """Get plant by ID with facilities and equipment IDs"""
        # Get plant
        plant_row = await queries.get_by_id(conn, id=plant_id)
        if not plant_row:
            return None
        
        # Get facilities
        facility_rows = [row async for row in queries.get_facilities(conn, plant_id=plant_id)]
        facilities = []
        
        for facility_row in facility_rows:
            # Get equipment IDs for this facility
            equipment_rows = [row async for row in queries.get_equipment_ids_by_facility(
                conn,
                facility_id=facility_row['id']
            )]
            equipment_ids = [row['id'] for row in equipment_rows]
            
            facility = Facility(
                **facility_row,
                equipment_ids=equipment_ids
            )
            facilities.append(facility)
        
        return Plant(**plant_row, facilities=facilities)
    
    async def get_all(self, conn) -> PlantListResponse:
        """Get all plants as lightweight list"""
        plant_rows = [row async for row in queries.get_all_plants(conn)]
        plants = [PlantListItem(**row) for row in plant_rows]
        return PlantListResponse(items=plants)
    
    async def save(self, conn, plant: Plant, force: bool = False) -> Plant:
        """
        Save plant with facility synchronization and optimistic concurrency control.
        Must be called within transaction.
        
        Args:
            conn: Database connection
            plant_id: Plant ID
            plant: Plant data to save
            force: If True, ignore server_modified_at and mark extra children as deleted
        
        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
        """
        plant_id = plant.id
        # Get current state if exists
        current = await self.get_by_id(conn, plant_id)
        
        # New server_modified_at timestamp
        new_server_modified_at = datetime.now(timezone.utc)
        
        if current and not force:
            # Validate server_modified_at for existing plants
            if plant.server_modified_at is None:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="server_modified_at is required for updating existing plant",
                        server_modified_at=current.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Missing server_modified_at in request"
                            )
                        ]
                    )
                )
            
            if plant.server_modified_at != current.server_modified_at:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="Plant was modified by another client",
                        server_modified_at=current.server_modified_at,
                        client_modified_at=plant.server_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Timestamp mismatch",
                                server_value=current.server_modified_at.isoformat(),
                                client_value=plant.server_modified_at.isoformat()
                            )
                        ]
                    )
                )
            
            # Check for extra facilities on server
            current_facility_ids = {f.id for f in current.facilities if not f.is_deleted}
            incoming_facility_ids = {f.id for f in plant.facilities}
            extra_facility_ids = current_facility_ids - incoming_facility_ids
            
            if extra_facility_ids:
                raise ConcurrentModificationError(
                    ConflictError(
                        message="Extra child facilities exist on server",
                        server_modified_at=current.server_modified_at,
                        client_modified_at=plant.server_modified_at,
                        extra_child_ids=list(extra_facility_ids),
                        conflicts=[
                            ConflictDetail(
                                field="facilities",
                                message=f"Server has {len(extra_facility_ids)} extra facilities not in client request"
                            )
                        ]
                    )
                )
        
        # Upsert plant
        await queries.upsert_plant(
            conn,
            id=plant_id,
            name=plant.name,
            locked_by_device_id=plant.locked_by_device_id,
            locked_by_user_id=plant.locked_by_user_id,
            locked_at=plant.locked_at,
            is_deleted=plant.is_deleted,
            server_modified_at=new_server_modified_at
        )
        
        # Synchronize facilities
        await self._sync_facilities(conn, plant_id, plant.facilities, force)
        
        # Return updated aggregate
        result = await self.get_by_id(conn, plant_id)
        if result is None:
            raise ValueError(f"Plant {plant_id} not found after save")
        return result
    
    async def delete(self, conn, plant_id: UUID) -> bool:
        """Logically delete plant (must be called within transaction)"""
        result = await queries.delete_plant(conn, id=plant_id)
        return result is not None and "0" not in result
    
    async def lock(self, conn, plant_id: UUID, device_id: UUID, user_id: int) -> bool:
        """Lock plant for editing (must be called within transaction)"""
        result = await queries.lock_plant(
            conn,
            id=plant_id,
            device_id=device_id,
            user_id=user_id,
            locked_at=datetime.now(timezone.utc)
        )
        return result is not None and "0" not in result
    
    async def unlock(self, conn, plant_id: UUID) -> bool:
        """Unlock plant (must be called within transaction)"""
        result = await queries.unlock_plant(conn, id=plant_id)
        return result is not None and "0" not in result
    
    async def _sync_facilities(self, conn, plant_id: UUID, facilities: list[Facility], force: bool):
        """
        Synchronize facilities: match by ID, add new, mark removed as deleted.
        
        Args:
            conn: Database connection
            plant_id: Plant ID
            facilities: List of facilities to sync
            force: If True, mark extra facilities as deleted; if False, extras already validated
        """
        # Get existing facility IDs for this plant
        existing_rows = [row async for row in queries.get_facility_ids(conn, plant_id=plant_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {f.id for f in facilities}
        
        # Validate that facilities being added/updated don't belong to another plant (never allow stealing)
        for facility in facilities:
            if facility.id not in existing_ids:
                # This is a new facility or existing facility from another plant
                # Check if it exists in another plant
                existing_plant_row = await queries.get_facility_plant_id(conn, facility_id=facility.id)
                if existing_plant_row and existing_plant_row['plant_id'] != plant_id:
                    raise ValueError(
                        f"Cannot transfer facility {facility.id} from another plant "
                        f"({existing_plant_row['plant_id']}). Child entities cannot be stolen."
                    )
        
        # Update or insert facilities with their is_deleted values
        for facility in facilities:
            await queries.upsert_facility(
                conn,
                id=facility.id,
                plant_id=plant_id,
                name=facility.name,
                is_deleted=facility.is_deleted
            )
        
        # Mark removed facilities as deleted (logical deletion)
        # This happens in both force and non-force modes (non-force already validated no extras)
        to_delete = existing_ids - incoming_ids
        for facility_id in to_delete:
            await queries.mark_facility_deleted(conn, id=facility_id)