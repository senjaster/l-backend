"""Group repository with hierarchical structure and plant synchronization"""
import aiosql
import logging

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass

from app.config import settings
from app.constants import DEFAULT_MODIFIED_SINCE
from app.exceptions import ConcurrentModificationError
from app.models.group import Group, GroupListItem, GroupListResponse, GroupPathResponse
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
        # Get group
        if include_deleted:
            group_row = await queries.get_by_id(conn, id=group_id)
        else:
            # Используем запрос с фильтром is_deleted = false
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
            plant_ids=plant_ids
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

    async def get_root_groups(self, conn) -> List[GroupListItem]:
        """Get all root groups (no parent)"""
        group_rows = [
            row async for row in queries.get_root_groups(conn)
        ]
        return [GroupListItem(**row) for row in group_rows]

    async def get_group_tree(
        self, conn, root_id: Optional[UUID] = None, include_plants: bool = False
    ) -> List[Group]:
        """
        Get full group tree starting from root or all roots
        
        Args:
            conn: Database connection
            root_id: Root group ID (if None, returns all root groups)
            include_plants: Include plants in groups
        """
        if root_id:
            # Get single tree from root
            group = await self.get_by_id(conn, root_id, include_children=True, include_plants=include_plants)
            return [group] if group else []
        else:
            # Get all root groups with their trees
            roots = await self.get_root_groups(conn)
            result = []
            for root in roots:
                group = await self.get_by_id(conn, root.id, include_children=True, include_plants=include_plants)
                if group:
                    result.append(group)
            return result

    async def get_group_path(self, conn, group_id: UUID) -> GroupPathResponse:
        """Get the full path from root to group"""
        path_rows = [
            row async for row in queries.get_group_path(conn, group_id=group_id)
        ]
        if not path_rows:
            raise ValueError(f"Group {group_id} not found")
        
        items = [GroupListItem(**row) for row in path_rows]
        return GroupPathResponse(items=items)

    async def save(self, conn, group: Group, force: bool = False) -> Group:
        """Save group with conflict detection"""
        group_id = group.id
        
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
        
        # Save to database
        await queries.upsert_group(
            conn, 
            id=group_id, 
            name=group.name, 
            parent_group_id=group.parent_group_id, 
            is_deleted=group.is_deleted, 
            server_modified_at=new_server_modified_at
        )
        
        return group

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
        
        # Check group exists
        group = await queries.get_by_id_active(conn, id=group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        # Check plants exist
        existing_plants = [
            row async for row in queries.check_plants_exist(conn, plant_ids=plant_ids)
        ]
        existing_ids = {row["id"] for row in existing_plants}
        
        missing = set(plant_ids) - existing_ids
        if missing:
            raise ValueError(f"Plants not found: {', '.join(str(id) for id in missing)}")
        
        # Add plants using bulk query
        await queries.bulk_add_plants_to_group(conn, group_id=group_id, plant_ids=plant_ids)
        
        return len(plant_ids)

    async def remove_plant_from_group(
        self, conn, group_id: UUID, plant_id: UUID, hard_delete: bool = False
    ) -> bool:
        """
        Remove a plant from a group
        
        Args:
            conn: Database connection
            group_id: Group ID
            plant_id: Plant ID
            hard_delete: If True, permanently delete relationship
            
        Returns:
            bool: True if removed, False if not found
        """
        if hard_delete:
            result = await queries.remove_plant_from_group_hard(
                conn, group_id=group_id, plant_id=plant_id
            )
        else:
            result = await queries.remove_plant_from_group(
                conn, group_id=group_id, plant_id=plant_id
            )
        
        if isinstance(result, int):
            return result > 0
        return result is not None and "0" not in result

    async def remove_all_plants_from_group(
        self, conn, group_id: UUID, hard_delete: bool = False
    ) -> int:
        """
        Remove all plants from a group
        
        Args:
            conn: Database connection
            group_id: Group ID
            hard_delete: If True, permanently delete relationships
            
        Returns:
            int: Number of relationships removed
        """
        # Check group exists
        group = await queries.get_by_id(conn, id=group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")
        
        if hard_delete:
            result = await queries.remove_all_plants_from_group_hard(conn, group_id=group_id)
        else:
            result = await queries.remove_all_plants_from_group(conn, group_id=group_id)
        
        # Return count of affected rows
        if isinstance(result, int):
            return result
        return 0

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

    async def check_has_children(self, conn, group_id: UUID) -> bool:
        """Check if a group has any children"""
        result = await queries.check_group_has_children(conn, group_id=group_id)
        return result["has_children"] if result else False

    async def check_has_plants(self, conn, group_id: UUID) -> bool:
        """Check if a group has any plants directly"""
        result = await queries.check_group_has_plants(conn, group_id=group_id)
        return result["has_plants"] if result else False

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

    async def bulk_delete_groups(
        self, conn, group_ids: List[UUID], hard_delete: bool = False
    ) -> int:
        """
        Bulk delete groups
        
        Args:
            conn: Database connection
            group_ids: List of group IDs
            hard_delete: If True, permanently delete
            
        Returns:
            int: Number of groups deleted
        """
        if not group_ids:
            return 0
        
        deleted_count = 0
        for group_id in group_ids:
            if await self.delete(conn, group_id, hard_delete):
                deleted_count += 1
        
        return deleted_count

    async def get_all_children(
        self, conn, group_id: UUID, include_self: bool = False
    ) -> List[UUID]:
        """
        Get all descendant group IDs recursively
        
        Args:
            conn: Database connection
            group_id: Group ID
            include_self: Include the group itself in the list
        """
        rows = [
            row async for row in queries.get_all_children_recursive(conn, group_id=group_id)
        ]
        result = [row["id"] for row in rows]
        
        if include_self:
            # Add self at the beginning
            group = await queries.get_by_id(conn, id=group_id)
            if group:
                result.insert(0, group_id)
        
        return result

    async def get_groups_with_plant_count(self, conn) -> List[dict]:
        """
        Get all groups with count of direct plants
        
        Returns:
            List[dict]: Groups with plant_count field
        """
        rows = [
            row async for row in queries.get_groups_with_plant_count(conn)
        ]
        return [dict(row) for row in rows]

    async def get_groups_with_children_count(self, conn) -> List[dict]:
        """
        Get all groups with count of immediate children
        
        Returns:
            List[dict]: Groups with children_count field
        """
        rows = [
            row async for row in queries.get_groups_with_children_count(conn)
        ]
        return [dict(row) for row in rows]

    async def get_group_hierarchy_depth(self, conn, group_id: UUID) -> int:
        """
        Get the depth of a group in the hierarchy
        
        Args:
            conn: Database connection
            group_id: Group ID
            
        Returns:
            int: Depth (0 for root)
        """
        result = await queries.get_group_hierarchy_depth(conn, group_id=group_id)
        return result["hierarchy_depth"] if result else -1

    async def get_children_count(self, conn, group_id: UUID) -> int:
        """
        Get count of immediate children
        
        Args:
            conn: Database connection
            group_id: Group ID
        """
        children = [
            row async for row in queries.get_children(conn, group_id=group_id)
        ]
        return len(children)