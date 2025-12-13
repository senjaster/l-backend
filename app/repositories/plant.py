"""Plant repository"""
from typing import Optional, Union
from uuid import UUID
from datetime import datetime, timezone
import aiosql
from app.models.plant import Plant, Facility, PlantWrite, FacilityWrite, PlantListItem, PlantListResponse

# Load queries from single file
queries = aiosql.from_path("app/queries/plant.sql", "asyncpg")


class PlantRepository:
    """Repository for Plant aggregate with facility synchronization"""
    
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
        return PlantListResponse(plants=plants)
    
    async def save(self, conn, plant_id: UUID, plant: Union[Plant, PlantWrite]) -> Plant:
        """Save plant with facility synchronization (must be called within transaction)"""
        # Determine is_deleted value (PlantWrite doesn't have it, so default to False)
        is_deleted = plant.is_deleted if isinstance(plant, Plant) else False
        
        # Upsert plant
        await queries.upsert_plant(
            conn,
            id=plant_id,
            name=plant.name,
            locked_by_device_id=plant.locked_by_device_id,
            locked_by_user_id=plant.locked_by_user_id,
            locked_at=plant.locked_at,
            is_deleted=is_deleted,
            last_modified_at=plant.last_modified_at
        )
        
        # Synchronize facilities
        await self._sync_facilities(conn, plant_id, plant.facilities)
        
        # Return updated aggregate
        return await self.get_by_id(conn, plant_id)
    
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
    
    async def _sync_facilities(self, conn, plant_id: UUID, facilities: list[Union[Facility, FacilityWrite]]):
        """Synchronize facilities: match by ID, add new, mark removed as deleted"""
        # Get existing facility IDs for this plant
        existing_rows = [row async for row in queries.get_facility_ids(conn, plant_id=plant_id)]
        existing_ids = {row['id'] for row in existing_rows}
        
        incoming_ids = {f.id for f in facilities}
        
        # Validate that facilities being added/updated don't belong to another plant
        for facility in facilities:
            if facility.id not in existing_ids:
                # This is a new facility or existing facility from another plant
                # Check if it exists in another plant
                existing_plant_row = await queries.get_facility_plant_id(conn, facility_id=facility.id)
                if existing_plant_row and existing_plant_row['plant_id'] != plant_id:
                    raise ValueError(
                        f"Facility {facility.id} belongs to another plant "
                        f"({existing_plant_row['plant_id']}) and cannot be transferred"
                    )
        
        # Update or insert (is_deleted is always False for incoming facilities)
        for facility in facilities:
            await queries.upsert_facility(
                conn,
                id=facility.id,
                plant_id=plant_id,
                name=facility.name,
                is_deleted=False
            )
        
        # Mark removed facilities as deleted (logical deletion)
        to_delete = existing_ids - incoming_ids
        for facility_id in to_delete:
            await queries.mark_facility_deleted(conn, id=facility_id)