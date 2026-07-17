"""Group repository with hierarchical structure and plant synchronization"""
import aiosql
import logging

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List

from app.config import settings
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.group import Group, GroupListResponse
from app.utils.async_wrapper import AsyncWrapper
from app.utils.db_utils import OptimisticLockingValidator


logger = logging.getLogger(__name__)


# Load queries from single file
_queries = aiosql.from_path("app/queries/group.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class GroupRepository:
    """Repository for Group aggregate"""

    async def get_by_id(self, conn, group_id: UUID) -> Optional[Group]:
        """Get group by ID"""
        group_row = await queries.get_by_id(conn, id=group_id)
        if not group_row:
            return None

        return Group(
            id=group_row["id"],
            name=group_row["name"],
            parent_group_id=group_row["parent_group_id"],
            is_deleted=group_row["is_deleted"],
            server_modified_at=group_row["server_modified_at"],
        )

    async def get_all(
        self, conn, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> GroupListResponse:
        """Get all groups as lightweight list, optionally filtered by modification date"""
        group_rows = [
            row
            async for row in queries.get_all_groups(conn, modified_since=modified_since)
        ]
        groups = [Group(**row) for row in group_rows]
        return GroupListResponse(items=groups)

    async def save(self, conn, group: Group, force: bool = False) -> Group:
        """Save group with conflict detection.
        Must be called within a transaction.

        Args:
            conn: Database connection
            group: Group data to save
            force: If True, ignore server_modified_at validation

        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
            ValueError: If group structure is invalid (self-reference or cyclic dependency)
        """
        group_id = group.id
        current = await self.get_by_id(conn, group_id)

        new_server_modified_at = datetime.now(timezone.utc)

        if current and not (force or settings.disable_optimistic_locking):
            OptimisticLockingValidator.validate_object(
                server_obj=current,
                client_obj=group,
            )

        # Guard: self-reference
        if group.parent_group_id == group_id:
            raise ValueError("Group cannot be its own parent")

        # Guard: cycle in tree (only relevant when a parent is set and the group already exists)
        if group.parent_group_id and current:
            if await self._check_cyclic_dependency(conn, group_id, group.parent_group_id):
                raise ValueError("Moving this group would create a cyclic dependency")

        await queries.upsert_group(
            conn,
            id=group_id,
            name=group.name,
            parent_group_id=group.parent_group_id,
            is_deleted=group.is_deleted,
            server_modified_at=new_server_modified_at,
        )

        result = await self.get_by_id(conn, group_id)
        if result is None:
            raise ValueError(f"Group {group_id} not found after save")

        return result

    async def _check_cyclic_dependency(
        self, conn, group_id: UUID, new_parent_id: UUID
    ) -> bool:
        """Check if moving a group to a new parent would create a cyclic dependency.

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
                new_parent_id=new_parent_id,
            )

            if result is None:
                return False
            return bool(result["would_create_cycle"])

        except Exception as e:
            logger.error(f"Error checking cyclic dependency: {e}")
            raise ValueError(f"Failed to check cyclic dependency: {e}")
