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
        self, conn, group_id: UUID, 
        include_deleted: bool = False
    ) -> Optional[Group]:
        """
        Get group by ID with optional children and plants
        
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
                await self._validate_optimistic_locking(current, group) 
            
            await queries.upsert_group(
                conn, 
                id=group_id, 
                name=group.name, 
                parent_group_id=group.parent_group_id, 
                is_deleted=group.is_deleted, 
                server_modified_at=new_server_modified_at
            )
            
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

    async def _validate_optimistic_locking(self, current: Group, group: Group) -> None:
        """Validate optimistic locking constraints between current and incoming group data.
        
        Args:
            current: Current group state from database
            group: Incoming group data to validate
            
        Raises:
            ConcurrentModificationError: If concurrent modification detected
        """
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

        # Validate child plants
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
