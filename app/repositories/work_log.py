"""Work log repository"""
import aiosql
import asyncpg
import logging
import re

from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.work_log import (
    WorkLog,
    WorkLogListResponse,
    WorkLogInspector,
)
from app.models import ConflictError, ConflictDetail
from app.exceptions import ConcurrentModificationError, BusinessValidationError
from app.config import settings
from app.utils.async_wrapper import AsyncWrapper
from app.utils.datetime_utils import truncate_to_milliseconds
from app.utils.db_utils import OptimisticLockingValidator, CollectionConfig

logger = logging.getLogger(__name__)


# Load queries with configurable driver
_queries = aiosql.from_path("app/queries/work_log.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class WorkLogRepository:
    """Repository for WorkLog aggregate with inspector synchronization and optimistic concurrency control"""

    async def get_by_id(self, conn, work_log_id: UUID) -> Optional[WorkLog]:
        """Get work log by ID with inspectors"""
        work_log_row = await queries.get_by_id(conn, work_log_id=work_log_id)
        if not work_log_row:
            return None

        inspector_rows = [
            row async for row in queries.get_inspectors_by_work_log(
                conn, work_log_id=work_log_id
            )
        ]
        
        inspectors = [
            WorkLogInspector(**row) for row in inspector_rows
        ]

        work_log_data = dict(work_log_row)
        work_log_data['inspectors'] = inspectors
        return WorkLog(**work_log_data)

    async def get_all(
        self, conn, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> WorkLogListResponse:
        """Get all work logs as lightweight list, optionally filtered by modification date"""
        work_log_rows = [
            row
            async for row in queries.get_all_work_logs(
                conn, modified_since=modified_since
            )
        ]
        work_log_list = [WorkLog(**row) for row in work_log_rows]
        return WorkLogListResponse(items=work_log_list)

    async def get_by_plant_id(
        self, conn, plant_id: UUID, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> list[WorkLog]:
        """Get all work logs for plant (full aggregates)"""
        work_log_rows = [
            row
            async for row in queries.get_by_plant_id(
                conn, plant_id=plant_id, modified_since=modified_since
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        
        all_inspectors = {}
        for work_log_id in work_log_ids:
            inspector_rows = [
                row async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            all_inspectors[work_log_id] = [
                WorkLogInspector(**row) for row in inspector_rows
            ]

        work_log_list = []
        for work_log_row in work_log_rows:
            work_log_data = dict(work_log_row)
            work_log_data['inspectors'] = all_inspectors.get(work_log_row["id"], [])
            work_log = WorkLog(**work_log_data)
            work_log_list.append(work_log)

        return work_log_list

    async def save(
        self, conn, work_log: WorkLog, force: bool = False
    ) -> WorkLog:
        """
        Save work log with inspector synchronization and optimistic concurrency control.
        Must be called within transaction.

        Args:
            conn: Database connection
            work_log: WorkLog data to save
            force: If True, ignore server_modified_at and mark extra children as deleted

        Raises:
            ConcurrentModificationError: If concurrent modification detected (force=False)
        """
        try:
            work_log_id = work_log.id

            current = await self.get_by_id(conn, work_log_id)

            new_server_modified_at = datetime.now(timezone.utc)

            if current and not (force or settings.disable_optimistic_locking):
                OptimisticLockingValidator.validate_object(
                    server_obj=current,
                    client_obj=work_log,
                    collection_configs=[
                        CollectionConfig(
                            server_collection=current.inspectors,
                            client_collection=work_log.inspectors,
                            collection_name="inspectors"
                        )
                    ]
                )
            
            await queries.upsert_work_log(
                conn,
                id=work_log_id,
                started_at=work_log.started_at,
                completed_at=work_log.completed_at,
                installation_percentage=work_log.installation_percentage,
                inspector_id=work_log.inspector_id,
                plant_id=work_log.plant_id,
                is_deleted=work_log.is_deleted,
                server_modified_at=new_server_modified_at,
            )

            await self._sync_inspectors(
                conn, work_log_id, work_log.inspectors, force
            )

            result = await self.get_by_id(conn, work_log_id)
            if result is None:
                raise ValueError(f"Work log {work_log_id} not found after save")
        except Exception as e:
            logger.error(f"Error in WorkLogRepository.save: {e}", exc_info=True)
            raise
        return result

    async def _sync_inspectors(
        self, conn, work_log_id: UUID, inspectors: Sequence[WorkLogInspector], force: bool
    ):
        """
        Synchronize inspectors: match by inspector_id, add new, remove missing.

        Args:
            conn: Database connection
            work_log_id: Work log ID
            inspectors: List of inspectors to sync
            force: If True, remove extra inspectors; if False, extras already validated
        """
        try:
            existing_inspectors = [
                row async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            existing_ids = {row["inspector_id"] for row in existing_inspectors}

            incoming_ids = {inspector.inspector_id for inspector in inspectors}

            to_delete = existing_ids - incoming_ids
            
            for inspector in inspectors:
                await queries.upsert_work_log_inspector(
                    conn,
                    work_log_id=work_log_id,
                    inspector_id=inspector.inspector_id,
                )

            if to_delete:
                if force:
                    for inspector_id in to_delete:
                        await queries.delete_work_log_inspector(
                            conn, work_log_id=work_log_id, inspector_id=inspector_id
                        )
                else:
                    raise BusinessValidationError(
                        f"Cannot remove inspectors with IDs: {', '.join(map(str, to_delete))}. "
                        f"Use force=True to confirm removal."
                    )
        
        except asyncpg.ForeignKeyViolationError as e:
            # Извлекаем ID инспектора из ошибки
            match = re.search(r"\(inspector_id\)=\((\d+)\)", str(e))
            if match:
                inspector_id = match.group(1)
                raise BusinessValidationError(
                    f"Inspector with ID {inspector_id} does not exist"
                )
            raise BusinessValidationError(
                "One or more inspectors do not exist"
            )
