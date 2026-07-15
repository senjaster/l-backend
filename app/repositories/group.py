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
from app.models.group import Group, GroupListItem, GroupListResponse
from app.routers import group
from app.utils.async_wrapper import AsyncWrapper
from app.utils.db_utils import OptimisticLockingValidator, CollectionConfig


logger = logging.getLogger(__name__)


# Load queries from single file
_queries = aiosql.from_path("app/queries/group.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class GroupRepository:
    """Repository for Group aggregate with hierarchical structure and plant synchronization"""

    async def get_by_id(
        self, conn, group_id: UUID, 
        include_deleted: bool = False
    ) -> Optional[Group]:
        """
        Get group by ID with optional children
        
        Args:
            conn: Database connection
            group_id: Group ID
            include_deleted: Include deleted groups
        """
        if include_deleted:
            group_row = await queries.get_by_id(conn, id=group_id)
        else:
            group_row = await queries.get_by_id_active(conn, id=group_id) 
        if not group_row:
            return None

        return Group(
            id=group_row["id"],
            name=group_row["name"],
            parent_group_id=group_row["parent_group_id"],
            is_deleted=group_row["is_deleted"],
            server_modified_at=group_row["server_modified_at"]
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
                OptimisticLockingValidator.validate_object(
                    server_obj=current,
                    client_obj=group
                )
            
            await queries.upsert_group(
                conn, 
                id=group_id, 
                name=group.name, 
                parent_group_id=group.parent_group_id, 
                is_deleted=group.is_deleted, 
                server_modified_at=new_server_modified_at
            )

            if group.children:
                await self.save_children(conn, group_id, group.children, force=force)
            
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

    async def get_children(self, conn, parent_id: UUID) -> List[Group]:
        """Get immediate children of a group
        
        Args:
            conn: Database connection
            parent_id: Parent group ID
            
        Returns:
            List of child groups (non-deleted only)
        """
        children_rows = [
            row async for row in queries.get_children(conn, group_id=parent_id)
        ]
        
        children = []
        for row in children_rows:
            children.append(Group(
                id=row['id'],
                name=row['name'],
                parent_group_id=row['parent_group_id'],
                is_deleted=row['is_deleted'],
                server_modified_at=row['server_modified_at'],
                children=[]
            ))
        
        return children

    async def save_children(self, conn, parent_id: UUID, children: List[Group], force: bool = False):
        """Save all children of a group"""
        if not children:
            return
        
        current_children = await self.get_children(conn, parent_id)
        current_child_ids = {child.id for child in current_children}
        new_child_ids = {child.id for child in children}
        
        # Handle deletions - children that are in DB but not in the new list
        children_to_delete = current_child_ids - new_child_ids
        
        if force:
            # Hard delete removed children
            for child_id in children_to_delete:
                logger.info(f"[SAVE_CHILDREN] Hard deleting child {child_id}")
                await queries.delete_group(conn, child_id)
        else:
            # Soft delete removed children - mark as deleted directly
            for child in current_children:
                if child.id in children_to_delete and not child.is_deleted:
                    logger.info(f"[SAVE_CHILDREN] Soft deleting child {child.id}")
                    # Update the child directly in DB without calling save()
                    # This avoids the get_by_id issue with deleted groups
                    await queries.upsert_group(
                        conn,
                        id=child.id,
                        name=child.name,
                        parent_group_id=parent_id,
                        is_deleted=True,
                        server_modified_at=datetime.now(timezone.utc)
                    )
        
        # Save or update each child from the new list
        for child in children:
            if child.id not in children_to_delete:  # Only save if not marked for deletion
                logger.info(f"[SAVE_CHILDREN] Saving child {child.id}")
                # Ensure child has correct parent
                child.parent_group_id = parent_id
                
                # Create a copy without children to avoid recursion
                child_to_save = Group(
                    id=child.id,
                    name=child.name,
                    parent_group_id=parent_id,
                    is_deleted=child.is_deleted,
                    server_modified_at=child.server_modified_at,
                    children=[]  # Don't pass children to avoid deep recursion
                )
                await self.save(conn, child_to_save, force=force)
    
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
