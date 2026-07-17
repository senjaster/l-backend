import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from datetime import datetime

from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.group import Group, GroupListResponse
from app.models.inspector import AccessLevel
from app.repositories.group import GroupRepository
from app.database import get_db_connection
from app.dependencies.permissions import get_permission_service
from app.services.permission_service import PermissionService
from app.utils.db_utils import ConcurrentModificationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/group", tags=["group"])
group_repo = GroupRepository()


@router.get("/all", response_model=GroupListResponse)
async def get_all_groups(
    modified_since: datetime = Query(DEFAULT_MODIFIED_SINCE, description="Filter by modification date"),
    conn = Depends(get_db_connection)
) -> GroupListResponse:
    """Получение списка групп (синхронизация)"""
    return await group_repo.get_all(conn, modified_since=modified_since)


@router.get("/by_id/{group_id}", response_model=Group)
async def get_group(
    group_id: UUID,
    conn = Depends(get_db_connection)
) -> Group:
    """Получение группы по ID"""
    group = await group_repo.get_by_id(conn, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("", response_model=Group)
async def upsert_group(
    group: Group,
    force: bool = Query(
        default=False,
        description="If true, ignore server_modified_at and force update",
    ),
    conn=Depends(get_db_connection),
    permission_service: PermissionService = Depends(get_permission_service),
) -> Group:
    """
    Create or replace group.

    Rules:
    - force=false (default):
      - Validates server_modified_at for existing groups
      - Rejects if modified_at doesn't match (409)
      - Ignores server_modified_at for new groups
    - force=true:
      - Ignores server_modified_at validation
      - Forces update even if concurrent modification detected
    - Prevents cyclic dependencies when moving groups
    - Permission: User must have MODIFY access
    """
    try:
        async with conn.transaction():
            permission_service.require_access_level(AccessLevel.MODIFY)
            result = await group_repo.save(conn, group, force=force)

        return result

    except ConcurrentModificationError as e:
        logger.warning(
            "Concurrent modification detected for group",
            extra={
                "group_id": str(group.id),
                "conflict": e.conflict_error.model_dump(mode="json"),
            },
        )
        raise HTTPException(
            status_code=409, detail=e.conflict_error.model_dump(mode="json")
        )
    except ValueError as e:
        logger.warning(
            "Invalid group data", extra={"group_id": str(group.id), "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))

