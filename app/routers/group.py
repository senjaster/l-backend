import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.group import Group, GroupListItem, GroupListResponse, GroupRequest, AddPlantsToGroup, GroupPathResponse, GroupTreeResponse
from app.models.auth import TokenPayload
from app.repositories.group import GroupRepository
from app.database import get_db_connection
from app.dependencies.auth import get_token_payload
from app.dependencies.permissions import get_permission_service
from app.dependencies.ownership import get_ownership_validator
from app.services.ownership_validator import OwnershipValidator
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["groups"])
group_repo = GroupRepository()


@router.post("/", response_model=Group)
async def create_group(
    group_data: GroupRequest,
    conn = Depends(get_db_connection)
):
    """Создание новой группы"""
    try:
        group = await group_repo.create(
            conn,
            name=group_data.name,
            parent_group_id=group_data.parent_group_id
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/all", response_model=GroupListResponse)
async def get_all_groups(
    modified_since: datetime = Query(DEFAULT_MODIFIED_SINCE, description="Filter by modification date"),
    conn = Depends(get_db_connection)
):
    """Получение списка групп (синхронизация)"""
    return await group_repo.get_all(conn, modified_since=modified_since)


@router.get("/root", response_model=List[GroupListItem])
async def get_root_groups(
    conn = Depends(get_db_connection)
):
    """Получение корневых групп (без родителя)"""
    return await group_repo.get_root_groups(conn)


@router.get("/tree", response_model=GroupTreeResponse)
async def get_group_tree(
    root_id: Optional[UUID] = Query(None, description="Root group ID (if None, returns all root groups)"),
    include_plants: bool = Query(False, description="Include plants in groups"),
    conn = Depends(get_db_connection)
):
    """Получение полного дерева групп"""
    try:
        tree = await group_repo.get_group_tree(conn, root_id=root_id, include_plants=include_plants)
        return GroupTreeResponse(items=tree)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}", response_model=Group)
async def get_group(
    group_id: UUID,
    include_children: bool = Query(True, description="Include children groups"),
    include_plants: bool = Query(False, description="Include plants in group"),
    include_deleted: bool = Query(False, description="Include deleted groups"),
    conn = Depends(get_db_connection)
):
    """Получение группы по ID"""
    group = await group_repo.get_by_id(
        conn,
        group_id=group_id,
        include_children=include_children,
        include_plants=include_plants,
        include_deleted=include_deleted
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("/{group_id}", response_model=Group)
async def update_group(
    group_id: UUID,
    group_data: GroupRequest,
    conn = Depends(get_db_connection)
):
    """Полное обновление группы"""
    try:
        group = await group_repo.update(
            conn,
            group_id=group_id,
            name=group_data.name,
            parent_group_id=group_data.parent_group_id,
            force=False
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{group_id}", response_model=Group)
async def partial_update_group(
    group_id: UUID,
    group_data: GroupRequest,
    conn = Depends(get_db_connection)
):
    """Частичное обновление группы"""
    try:
        group = await group_repo.update(
            conn,
            group_id=group_id,
            name=group_data.name,
            parent_group_id=group_data.parent_group_id,
            force=False
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete"),
    conn = Depends(get_db_connection)
):
    """Удаление группы (мягкое или жесткое)"""
    deleted = await group_repo.delete(conn, group_id=group_id, hard_delete=hard_delete)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}


@router.get("/{group_id}/plants")
async def get_group_plants(
    group_id: UUID,
    include_subgroups: bool = Query(True, description="Include plants from subgroups"),
    conn = Depends(get_db_connection)
):
    """Получение всех станций в группе (и подгруппах)"""
    group = await group_repo.get_by_id(conn, group_id, include_children=False)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    plant_ids = await group_repo.get_plants_in_group(conn, group_id, include_subgroups)
    return {"items": plant_ids}


@router.post("/{group_id}/plants")
async def add_plants_to_group(
    group_id: UUID,
    request: AddPlantsToGroup,
    conn = Depends(get_db_connection)
):
    """Добавление станций в группу"""
    if not request.plant_ids:
        raise HTTPException(status_code=400, detail="Plant IDs list cannot be empty")
    
    try:
        added_count = await group_repo.add_plants_to_group(
            conn,
            group_id=group_id,
            plant_ids=request.plant_ids
        )
        return {"message": f"Added {added_count} plants to group"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{group_id}/plants/{plant_id}")
async def remove_plant_from_group(
    group_id: UUID,
    plant_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete relationship"),
    conn = Depends(get_db_connection)
):
    """Удаление станции из группы"""
    removed = await group_repo.remove_plant_from_group(
        conn,
        group_id=group_id,
        plant_id=plant_id,
        hard_delete=hard_delete
    )
    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Plant not found in this group"
        )
    return {"message": "Plant removed from group"}


@router.delete("/{group_id}/plants")
async def remove_all_plants_from_group(
    group_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete all relationships"),
    conn = Depends(get_db_connection)
):
    """Удаление всех станций из группы"""
    try:
        removed_count = await group_repo.remove_all_plants_from_group(
            conn,
            group_id=group_id,
            hard_delete=hard_delete
        )
        return {"message": f"Removed {removed_count} plants from group"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}/path", response_model=GroupPathResponse)
async def get_group_path(
    group_id: UUID,
    conn = Depends(get_db_connection)
):
    """Получение пути от корня до группы"""
    try:
        return await group_repo.get_group_path(conn, group_id=group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk/delete")
async def bulk_delete_groups(
    group_ids: List[UUID],
    hard_delete: bool = Query(False, description="Permanently delete"),
    conn = Depends(get_db_connection)
):
    """Массовое удаление групп"""
    if not group_ids:
        raise HTTPException(status_code=400, detail="Group IDs list cannot be empty")
    
    deleted_count = await group_repo.bulk_delete_groups(
        conn,
        group_ids=group_ids,
        hard_delete=hard_delete
    )
    return {"message": f"Deleted {deleted_count} groups"}


@router.post("/{group_id}/move")
async def move_group(
    group_id: UUID,
    new_parent_id: Optional[str] = None,
    conn = Depends(get_db_connection)
):
    """Перемещение группы в другую родительскую группу"""
    try:
        print(f"Received request to move group {group_id} to new parent {new_parent_id}")
        parent_uuid = None
        if new_parent_id and new_parent_id.strip():
            try:
                parent_uuid = UUID(new_parent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format")
        group = await group_repo.move_group(
            conn,
            group_id=group_id,
            new_parent_id=parent_uuid
        )
        return {
            "message": "Group moved successfully",
            "group_id": str(group.id),
            "new_parent_id": str(group.parent_group_id) if group.parent_group_id else None
        }
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        elif "cyclic" in error_msg or "self" in error_msg:
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}/children")
async def get_group_children(
    group_id: UUID,
    include_deleted: bool = Query(False, description="Include deleted children"),
    conn = Depends(get_db_connection)
):
    """Получение непосредственных детей группы"""
    group = await group_repo.get_by_id(conn, group_id, include_children=False)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    children = []
    child_rows = []
    full_group = await group_repo.get_by_id(
        conn,
        group_id=group_id,
        include_children=True,
        include_plants=False
    )
    return {"items": full_group.children if full_group else []}


@router.get("/{group_id}/descendants")
async def get_group_descendants(
    group_id: UUID,
    conn = Depends(get_db_connection)
):
    """Получение всех потомков группы"""
    group = await group_repo.get_by_id(conn, group_id, include_children=False)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    descendants = await group_repo.get_all_children(conn, group_id, include_self=False)
    return {"items": descendants}


@router.get("/by-plant/{plant_id}")
async def get_groups_by_plant(
    plant_id: UUID,
    conn = Depends(get_db_connection)
):
    """Получение всех групп, содержащих станцие"""
    groups = await group_repo.get_groups_by_plant(conn, plant_id=plant_id)
    return {"items": groups}


@router.get("/{group_id}/check")
async def check_group_status(
    group_id: UUID,
    conn = Depends(get_db_connection)
):
    """Проверка статуса группы (есть ли дети или станция)"""
    group = await group_repo.get_by_id(conn, group_id, include_children=False)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    has_children = await group_repo.check_has_children(conn, group_id)
    has_plants = await group_repo.check_has_plants(conn, group_id)
    
    return {
        "group_id": group_id,
        "has_children": has_children,
        "has_plants": has_plants
    }


@router.get("/{group_id}/depth")
async def get_group_depth(
    group_id: UUID,
    conn = Depends(get_db_connection)
):
    """Получение глубины группы в иерархии"""
    group = await group_repo.get_by_id(conn, group_id, include_children=False)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    depth = await group_repo.get_group_hierarchy_depth(conn, group_id)
    return {"group_id": group_id, "depth": depth}