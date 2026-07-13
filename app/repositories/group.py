"""Group repository with hierarchical structure and plant synchronization"""
import aiosql
import logging

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError

from app.config import settings
from app.constants import DEFAULT_MODIFIED_SINCE
from app.exceptions import ConcurrentModificationError
from app.models.group import Group, GroupListItem, GroupListResponse
from app.models.plant import Plant
from app.models import ConflictError, ConflictDetail
from app.utils.async_wrapper import AsyncWrapper
from app.utils.datetime_utils import truncate_to_milliseconds

logger = logging.getLogger(__name__)

# Load queries from single file
_queries = aiosql.from_path("app/queries/group.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class GroupRepository:
    """Repository for Group aggregate with hierarchical structure and plant synchronization"""

    async def get_by_id(
        self, conn, group_id: UUID, include_children: bool = True, 
        include_plants: bool = False, include_deleted: bool = False
    ) -> Optional[Group]:
        """
        Get group by ID with optional children and plants
        
        Args:
            conn: Database connection
            group_id: Group ID
            include_children: Include children groups recursively
            include_plants: Include plants in the group
            include_deleted: Include deleted groups
        """
        if include_deleted:
            group_row = await queries.get_by_id(conn, id=group_id)
        else:
            group_row = await queries.get_by_id_active(conn, id=group_id) 
        if not group_row:
            return None

        # Get plant IDs if requested
        plant_ids = []
        if include_plants:
            plant_rows = [
                row async for row in queries.get_plant_ids_by_group(conn, group_id=group_id)
            ]
            plant_ids = [row["plant_id"] for row in plant_rows]

        # Get children recursively if requested
        children = []
        if include_children:
            children = await self._get_children_tree(conn, group_id, include_plants)

        return Group(
            id=group_row["id"],
            name=group_row["name"],
            parent_group_id=group_row["parent_group_id"],
            is_deleted=group_row["is_deleted"],
            server_modified_at=group_row["server_modified_at"],
            children=children,
        )

    async def get_all(
        self, conn, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> GroupListResponse:
        """Get all groups as lightweight list, optionally filtered by modification date"""
        group_rows = [
            row
            async for row in queries.get_all_groups(conn, modified_since=modified_since)
        ]
        groups = [GroupListItem(**row) for row in group_rows]
        return GroupListResponse(items=groups)

    async def create(
        self, conn, name: str, parent_group_id: Optional[UUID] = None
    ) -> Group:
        """
        Create a new group
        
        Args:
            conn: Database connection
            name: Group name
            parent_group_id: Parent group ID (optional)
        """
        group_id = uuid4()
        now = datetime.now(timezone.utc)
        
        # Validate parent exists if provided
        if parent_group_id:
            parent = await queries.get_by_id(conn, id=parent_group_id)
            if not parent:
                raise ValueError(f"Parent group {parent_group_id} not found")
        
        await queries.upsert_group(
            conn,
            id=group_id,
            name=name,
            parent_group_id=parent_group_id,
            is_deleted=False,
            server_modified_at=now,
        )
        
        return await self.get_by_id(conn, group_id)
    
    async def update(
        self, conn, group_id: UUID, name: Optional[str] = None, 
        parent_group_id: Optional[UUID] = None, force: bool = False
    ) -> Group:
        """
        Update a group with optimistic concurrency control
        
        Args:
            conn: Database connection
            group_id: Group ID
            name: New name (optional)
            parent_group_id: New parent (optional)
            force: If True, ignore concurrency checks
            
        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
            ValueError: If validation fails
        """
        # Get current state
        current = await self.get_by_id(conn, group_id, include_children=False)
        if not current:
            raise ValueError(f"Group {group_id} not found")
        
        # Validate parent if provided
        if parent_group_id is not None:
            # Check self-reference
            if parent_group_id == group_id:
                raise ValueError("Group cannot be its own parent")
            
            # Check parent exists
            if parent_group_id:
                parent = await queries.get_by_id(conn, id=parent_group_id)
                if not parent:
                    raise ValueError(f"Parent group {parent_group_id} not found")
                
                # Check cyclic dependency
                result = await queries.check_cyclic_dependency(
                    conn, group_id=group_id, new_parent_id=parent_group_id
                )
                
                if result and result.get("would_create_cycle", False):
                    raise ValueError("Cyclic dependency detected")
                
        # Build update data
        new_name = name if name is not None else current.name
        new_parent = parent_group_id if parent_group_id is not None else current.parent_group_id
        
        now = datetime.now(timezone.utc)
        
        await queries.upsert_group(
            conn,
            id=group_id,
            name=new_name,
            parent_group_id=new_parent,
            is_deleted=current.is_deleted,
            server_modified_at=now,
        )
        
        return await self.get_by_id(conn, group_id)

    async def save(self, conn, group: Group, force: bool = False) -> Group:
        """Save group with conflict detection
        Must be called within transaction.
        
        Args:
            conn: Database connection
            group: Group data to save
            force: If True, ignore server_modified_at and mark extra children as deleted

        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
        """
        group_id = group.id
        
        try:
            current = await self.get_by_id(conn, group_id)
            
            new_server_modified_at = datetime.now(timezone.utc)
            
            if current and not (force or settings.disable_optimistic_locking):
                # Validate server_modified_at
                if current.server_modified_at != group.server_modified_at:
                    raise ConcurrentModificationError(
                        conflict_error=ConflictError(
                            server_modified_at=current.server_modified_at,
                            client_modified_at=group.server_modified_at
                        )
                    )
                
                if truncate_to_milliseconds(
                    group.server_modified_at
                ) != truncate_to_milliseconds(current.server_modified_at):
                    raise ConcurrentModificationError(
                        ConflictError(
                            message="Group was modified by another client",
                            server_modified_at=current.server_modified_at,
                            client_modified_at=group.server_modified_at,
                            conflicts=[
                                ConflictDetail(
                                    field="server_modified_at",
                                    message="Timestamp mismatch",
                                    server_value=current.server_modified_at.isoformat(),
                                    client_value=group.server_modified_at.isoformat(),
                                )
                            ],
                        )
                    )

                current_plant_ids = {
                    f.id for f in current.plants if not f.is_deleted
                }
                incoming_plant_ids = {f.id for f in group.plants}
                extra_plant_ids = current_plant_ids - incoming_plant_ids

                if extra_plant_ids:
                    raise ConcurrentModificationError(
                        ConflictError(
                            message="Extra child plants exist on server",
                            server_modified_at=current.server_modified_at,
                            client_modified_at=group.server_modified_at,
                            extra_child_ids=list(extra_plant_ids),
                            conflicts=[
                                ConflictDetail(
                                    field="plants",
                                    message=f"Server has {len(extra_plant_ids)} extra plants not in client request",
                                )
                            ],
                        )
                    )
            
            await queries.upsert_group(
                conn, 
                id=group_id, 
                name=group.name, 
                parent_group_id=group.parent_group_id, 
                is_deleted=group.is_deleted, 
                server_modified_at=new_server_modified_at
            )

            await self._sync_plants(conn, group_id, group.plants, force=True)
            
            result = await self.get_by_id(conn, group_id)
            if result is None:
                raise ValueError(f"Group {group_id} not found after save")
            
            return result
        
        except ForeignKeyViolationError as e:
            raise ValueError(f"Parent group with id {group.parent_group_id} not found") from e
            
        except UniqueViolationError as e:
            raise ValueError(f"Group with id {group_id} already exists") from e
            
        except Exception as e:
            raise

    async def add_plants_to_group(
        self, conn, group_id: UUID, plant_ids: List[UUID]
    ) -> int:
        """
        Add plants to a group
        
        Args:
            conn: Database connection
            group_id: Group ID
            plant_ids: List of plant IDs
            
        Returns:
            int: Number of plants added
            
        Raises:
            ValueError: If group not found or plants don't exist
        """
        if not plant_ids:
            return 0
        
        group = await queries.get_by_id_active(conn, id=group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        existing_plants = [
            row async for row in queries.check_plants_exist(conn, plant_ids=plant_ids)
        ]
        existing_ids = {row["id"] for row in existing_plants}
        
        missing = set(plant_ids) - existing_ids
        if missing:
            raise ValueError(f"Plants not found: {', '.join(str(id) for id in missing)}")
        
        await queries.bulk_add_plants_to_group(conn, group_id=group_id, plant_ids=plant_ids)
        
        return len(plant_ids)

    async def get_plants_in_group(
        self, conn, group_id: UUID, include_subgroups: bool = True
    ) -> List[UUID]:
        """
        Get all plant IDs in a group (and optionally its descendants)
        
        Args:
            conn: Database connection
            group_id: Group ID
            include_subgroups: Include plants from subgroups
            
        Returns:
            List[UUID]: List of plant IDs
        """
        if include_subgroups:
            plant_rows = [
                row async for row in queries.get_plant_ids_by_group_recursive(conn, group_id=group_id)
            ]
        else:
            plant_rows = [
                row async for row in queries.get_plant_ids_by_group(conn, group_id=group_id)
            ]
        
        return [row["plant_id"] for row in plant_rows]

    async def get_groups_by_plant(self, conn, plant_id: UUID) -> List[GroupListItem]:
        """Get all groups that contain a plant"""
        group_rows = [
            row async for row in queries.get_groups_by_plant(conn, plant_id=plant_id)
        ]
        return [GroupListItem(**row) for row in group_rows]

    async def _check_cyclic_dependency(
        self, conn, group_id: UUID, new_parent_id: UUID
    ) -> bool:
        """
        Check if moving a group to a new parent would create a cyclic dependency.
        
        Args:
            conn: Database connection
            group_id: UUID of the group being moved
            new_parent_id: UUID of the proposed new parent group
            
        Returns:
            bool: True if moving would create a cycle, False otherwise
        """
        try:
            result = await queries.check_cyclic_dependency(
                conn, 
                group_id=group_id, 
                new_parent_id=new_parent_id
            )
            
            if result and isinstance(result, dict):
                return result.get("would_create_cycle", False)
            return False
            
        except Exception as e:
            logger.error(f"Error checking cyclic dependency: {e}")
            raise ValueError(f"Failed to check cyclic dependency: {e}")
    
    async def _get_children_tree(
        self, conn, parent_id: UUID, include_plants: bool = False
    ) -> List[Group]:
        """
        Recursively build children tree
        
        Args:
            conn: Database connection
            parent_id: Parent group ID
            include_plants: Include plants in groups
        """
        child_rows = [
            row async for row in queries.get_children(conn, group_id=parent_id)
        ]
        
        children = []
        for child_row in child_rows:
            # Get children recursively
            grandchildren = await self._get_children_tree(conn, child_row["id"], include_plants)
            
            # Get plant IDs if requested
            plants = []
            plant_ids = []
            if include_plants:
                plant_rows = [
                    row async for row in queries.get_plants_by_group(conn, group_id=child_row["id"])
                ]
                plants = [Plant(**row) for row in plant_rows]
                plant_ids = [p.id for p in plants]
            
            child = Group(
                id=child_row["id"],
                name=child_row["name"],
                parent_group_id=child_row["parent_group_id"],
                is_deleted=child_row["is_deleted"],
                server_modified_at=child_row["server_modified_at"],
                children=grandchildren,
                plants=plants
            )
            children.append(child)
        
        return children

    async def _sync_plants(
        self, conn, group_id: UUID, plants: list[Plant], force: bool
    ):
        """
        Synchronize plants: match by ID, add new, mark removed as deleted.

        Args:
            conn: Database connection
            group_id: Group ID
            plants: List of plants to sync
            force: If True, mark extra plants as deleted; if False, extras already validated
        """
        # Get existing plant IDs for this group
        existing_rows = [
            row async for row in queries.get_plant_ids_by_group(conn, group_id=group_id)
        ]
        existing_ids = {row["id"] for row in existing_rows}

        incoming_ids = {f.id for f in plants}

        # Validate that groups being added/updated don't belong to another group (never allow stealing)
        for plant in plants:
            if plant.id not in existing_ids:
                # This is a new plant or existing plant from another plant
                # Check if it exists in another plant
                existing_group_row = await queries.get_plant_group_id(
                    conn, plant_id=plant.id
                )
                if existing_group_row and existing_group_row["group_id"] != group_id:
                    raise ValueError(
                        f"Cannot transfer group {plant.id} from another plant "
                        f"({existing_group_row['group_id']}). Child entities cannot be stolen."
                    )

        # Update or insert plants with their is_deleted values
        for plant in plants:
            await queries.upsert_plant(
                conn,
                id=plant.id,
                group_id=group_id,
                name=plant.name,
                claimed_by_device_id=plant.claimed_by_device_id,
                claimed_by_user_id=plant.claimed_by_user_id,
                claimed_at=plant.claimed_at,
                is_deleted=plant.is_deleted,
                server_modified_at=plant.server_modified_at,
                facilities=plant.facilities
            )

        # Mark removed plants as deleted (logical deletion)
        # This happens in both force and non-force modes (non-force already validated no extras)
        to_delete = existing_ids - incoming_ids
        for group_id in to_delete:
            await queries.mark_plant_deleted(conn, id=group_id)