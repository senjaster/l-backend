"""Work log repository"""
import aiosql
import logging

from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.work_log import (
    WorkLog,
    WorkLogListResponse,
    WorkLogInspector,
)
from app.models import ConflictError, ConflictDetail
from app.exceptions import ConcurrentModificationError
from app.config import settings
from app.utils.async_wrapper import AsyncWrapper
from app.utils.datetime_utils import truncate_to_milliseconds

logger = logging.getLogger(__name__)


# Load queries with configurable driver
_queries = aiosql.from_path("app/queries/work_log.sql", settings.db_driver)
queries = AsyncWrapper(_queries) if settings.db_driver == "psycopg2" else _queries


class WorkLogRepository:
    """Repository for WorkLog aggregate with inspector synchronization and optimistic concurrency control"""

    def _build_work_log_aggregates(
        self, work_log_rows: list, inspector_rows: list
    ) -> list[WorkLog]:
        """
        Build WorkLog aggregates from separate row lists.

        Args:
            work_log_rows: List of work log rows
            inspector_rows: List of inspector rows (must have work_log_id)

        Returns:
            List of WorkLog instances
        """
        # Group inspectors by work_log_id
        inspectors_by_work_log = {}
        for row in inspector_rows:
            work_log_id = row["work_log_id"]
            if work_log_id not in inspectors_by_work_log:
                inspectors_by_work_log[work_log_id] = []
            inspectors_by_work_log[work_log_id].append(
                WorkLogInspector(
                    work_log_id=work_log_id,
                    inspector_id=row["inspector_id"],
                )
            )

        work_log_list = []
        for work_log_row in work_log_rows:
            work_log_id = work_log_row["id"]
            work_log_data = {k: v for k, v in work_log_row.items()}
            work_log_data["inspectors"] = inspectors_by_work_log.get(work_log_id, [])
            work_log = WorkLog(**work_log_data)
            work_log_list.append(work_log)

        return work_log_list

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

        work_log_list = self._build_work_log_aggregates(
            [work_log_row], inspector_rows
        )

        return work_log_list[0] if work_log_list else None

    async def get_by_id_with_username(self, conn, work_log_id: UUID) -> Optional[WorkLog]:
        """Get work log by ID with inspector username"""
        work_log_row = await queries.get_by_id_with_username(
            conn, work_log_id=work_log_id
        )
        if not work_log_row:
            return None

        inspector_rows = [
            row async for row in queries.get_inspectors_by_work_log(
                conn, work_log_id=work_log_id
            )
        ]

        work_log_list = self._build_work_log_aggregates(
            [work_log_row], inspector_rows
        )

        return work_log_list[0] if work_log_list else None

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
        """Get all work logs for plant (full aggregates) - uses batch queries for efficiency"""
        work_log_rows = [
            row
            async for row in queries.get_by_plant_id(
                conn, plant_id=plant_id, modified_since=modified_since
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(
            work_log_rows, inspector_rows
        )

    async def get_by_inspector_id(
        self, conn, inspector_id: int, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> list[WorkLog]:
        """Get all work logs for inspector (full aggregates)"""
        work_log_rows = [
            row
            async for row in queries.get_by_inspector_id(
                conn, inspector_id=inspector_id, modified_since=modified_since
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(work_log_rows, inspector_rows)

    async def get_by_date_range(
        self,
        conn,
        start_date: datetime,
        end_date: datetime,
        plant_id: Optional[UUID] = None,
        inspector_id: Optional[int] = None,
    ) -> list[WorkLog]:
        """Get work logs within date range with optional filters"""
        work_log_rows = [
            row
            async for row in queries.get_by_date_range(
                conn,
                start_date=start_date,
                end_date=end_date,
                plant_id=plant_id,
                inspector_id=inspector_id,
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(work_log_rows, inspector_rows)

    async def get_work_logs_by_inspector(
        self, conn, inspector_id: int, modified_since: datetime = DEFAULT_MODIFIED_SINCE
    ) -> list[WorkLog]:
        """Get work logs where inspector is assigned (including through work_log_inspector table)"""
        work_log_rows = [
            row
            async for row in queries.get_work_logs_by_inspector_id(
                conn, inspector_id=inspector_id, modified_since=modified_since
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(work_log_rows, inspector_rows)

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
                if work_log.server_modified_at is None:
                    raise ConcurrentModificationError(
                        ConflictError(
                            message="server_modified_at is required for updating existing work log",
                            server_modified_at=current.server_modified_at,
                            conflicts=[
                                ConflictDetail(
                                    field="server_modified_at",
                                    message="Missing server_modified_at in request",
                                )
                            ],
                        )
                    )

                if truncate_to_milliseconds(
                    work_log.server_modified_at
                ) != truncate_to_milliseconds(current.server_modified_at):
                    raise ConcurrentModificationError(
                        ConflictError(
                            message="Work log was modified by another client",
                            server_modified_at=current.server_modified_at,
                            client_modified_at=work_log.server_modified_at,
                            conflicts=[
                                ConflictDetail(
                                    field="server_modified_at",
                                    message="Timestamp mismatch",
                                    server_value=current.server_modified_at.isoformat(),
                                    client_value=work_log.server_modified_at.isoformat(),
                                )
                            ],
                        )
                    )

                current_inspector_ids = {
                    inspector.inspector_id for inspector in current.inspectors
                }
                incoming_inspector_ids = {inspector.inspector_id for inspector in work_log.inspectors}
                extra_inspector_ids = current_inspector_ids - incoming_inspector_ids
                
                if extra_inspector_ids:
                    raise ConcurrentModificationError(
                        ConflictError(
                            message="Extra inspectors exist on server",
                            server_modified_at=current.server_modified_at,
                            client_modified_at=work_log.server_modified_at,
                            extra_child_ids=list(extra_inspector_ids),
                            conflicts=[
                                ConflictDetail(
                                    field="inspectors",
                                    message=f"Server has {len(extra_inspector_ids)} extra inspectors not in client request",
                                )
                            ],
                        )
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

    async def delete(self, conn, work_log_id: UUID) -> bool:
        """Logically delete work log (must be called within transaction)"""
        result = await queries.delete_work_log(conn, work_log_id=work_log_id)
        return result is not None and "0" not in result

    async def restore(self, conn, work_log_id: UUID) -> bool:
        """Restore logically deleted work log"""
        result = await queries.restore_work_log(conn, work_log_id=work_log_id)
        return result is not None and "0" not in result

    async def update_status(
        self,
        conn,
        work_log_id: UUID,
        completed_at: Optional[datetime],
        installation_percentage: Optional[float],
    ) -> Optional[WorkLog]:
        """
        Update work log completion status.
        Must be called within transaction.
        """
        await queries.update_work_log_status(
            conn,
            work_log_id=work_log_id,
            completed_at=completed_at,
            installation_percentage=installation_percentage,
        )
        return await self.get_by_id(conn, work_log_id)

    async def get_active_work_logs_by_plant(
        self, conn, plant_id: UUID
    ) -> list[WorkLog]:
        """Get active (not completed) work logs for a plant"""
        work_log_rows = [
            row
            async for row in queries.get_active_work_logs_by_plant(
                conn, plant_id=plant_id
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(work_log_rows, inspector_rows)

    async def get_completed_work_logs_by_plant(
        self, conn, plant_id: UUID, start_date: datetime, end_date: datetime
    ) -> list[WorkLog]:
        """Get completed work logs for a plant within date range"""
        work_log_rows = [
            row
            async for row in queries.get_completed_work_logs_by_plant(
                conn,
                plant_id=plant_id,
                start_date=start_date,
                end_date=end_date,
            )
        ]

        if not work_log_rows:
            return []

        work_log_ids = [row["id"] for row in work_log_rows]
        inspector_rows = []
        for work_log_id in work_log_ids:
            inspectors = [
                row
                async for row in queries.get_inspectors_by_work_log(
                    conn, work_log_id=work_log_id
                )
            ]
            inspector_rows.extend(inspectors)

        return self._build_work_log_aggregates(work_log_rows, inspector_rows)

    async def get_installation_stats_by_plant(
        self, conn, plant_id: UUID
    ) -> dict:
        """Get installation statistics by plant"""
        row = await queries.get_installation_stats_by_plant(
            conn, plant_id=plant_id
        )
        return dict(row) if row else {}

    async def get_installation_stats_by_inspector(
        self, conn, inspector_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict:
        """Get installation statistics by inspector"""
        row = await queries.get_installation_stats_by_inspector(
            conn,
            inspector_id=inspector_id,
            start_date=start_date,
            end_date=end_date,
        )
        return dict(row) if row else {}

    async def get_work_log_summary_by_period(
        self, conn, start_date: datetime, end_date: datetime, plant_id: Optional[UUID] = None
    ) -> list[dict]:
        """Get work log summary grouped by day/week/month"""
        rows = [
            row
            async for row in queries.get_work_log_summary_by_period(
                conn, start_date=start_date, end_date=end_date, plant_id=plant_id
            )
        ]
        return [dict(row) for row in rows]

    async def get_work_log_timeline(
        self, conn, plant_id: UUID, days_back: int
    ) -> list[dict]:
        """Get timeline of work log activity for a plant"""
        rows = [
            row
            async for row in queries.get_work_log_timeline(
                conn, plant_id=plant_id, days_back=days_back
            )
        ]
        return [dict(row) for row in rows]

    async def get_inspector_performance(
        self, conn, inspector_id: int, start_date: datetime, end_date: datetime
    ) -> Optional[dict]:
        """Get performance metrics for a specific inspector"""
        row = await queries.get_inspector_performance(
            conn,
            inspector_id=inspector_id,
            start_date=start_date,
            end_date=end_date,
        )
        return dict(row) if row else None

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
        existing_inspectors = [
            row async for row in queries.get_inspectors_by_work_log(
                conn, work_log_id=work_log_id
            )
        ]
        existing_ids = {row["inspector_id"] for row in existing_inspectors}

        incoming_ids = {inspector.inspector_id for inspector in inspectors}

        for inspector in inspectors:
            await queries.upsert_work_log_inspector(
                conn,
                work_log_id=work_log_id,
                inspector_id=inspector.inspector_id,
            )

        if force:
            to_delete = existing_ids - incoming_ids
            for inspector_id in to_delete:
                await queries.delete_work_log_inspector(
                    conn, work_log_id=work_log_id, inspector_id=inspector_id
                )

