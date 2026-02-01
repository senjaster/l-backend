"""Defect router - implements new API design principles

Defects are NOT owned by plant claims - they can be modified by any authenticated user.
This is the key reason for separating defects from the equipment aggregate.
"""

from uuid import UUID
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.defect import Defect, DefectListResponse
from app.repositories.defect import DefectRepository, ConcurrentModificationError
from app.database import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/defect", tags=["defect"])
defect_repo = DefectRepository()


@router.get("/all", response_model=DefectListResponse)
async def get_all_defects(
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return defects modified after this timestamp",
    ),
    conn=Depends(get_db_connection),
):
    """Get all defect IDs (lightweight list), optionally filtered by modification date"""
    return await defect_repo.get_all(conn, modified_since=modified_since)


@router.get("/by_id/{defect_id}", response_model=Defect)
async def get_defect_by_id(defect_id: UUID, conn=Depends(get_db_connection)):
    """Get specific defect"""
    defect = await defect_repo.get_by_id(conn, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@router.get("/by_plant_id/{plant_id}", response_model=list[Defect])
async def get_defects_by_plant_id(
    plant_id: UUID,
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return defects modified after this timestamp",
    ),
    conn=Depends(get_db_connection),
):
    """Get all defects for a plant (full data), optionally filtered by modification date"""
    return await defect_repo.get_by_plant_id(
        conn, plant_id, modified_since=modified_since
    )


@router.put("", response_model=Defect)
async def upsert_defect(
    defect: Defect,
    force: bool = Query(
        default=False,
        description="If true, ignore server_modified_at validation",
    ),
    conn=Depends(get_db_connection),
):
    """
    Create or replace defect.

    Rules:
    - force=false (default):
      - Validates server_modified_at for existing defects
      - Ignores server_modified_at for new defects
    - force=true:
      - Ignores server_modified_at validation
    
    Note: Defects are NOT owned by plant claims and can be modified by any authenticated user.
    This is the key difference from equipment, which requires plant ownership.
    """
    try:
        async with conn.transaction():
            result = await defect_repo.save(conn, defect, force=force)
        return result
    except ConcurrentModificationError as e:
        logger.warning(
            "Concurrent modification detected for defect",
            extra={
                "defect_id": str(defect.id),
                "conflict": e.conflict_error.model_dump(mode="json"),
            },
        )
        raise HTTPException(
            status_code=409, detail=e.conflict_error.model_dump(mode="json")
        )
    except ValueError as e:
        logger.warning(
            "Invalid defect data",
            extra={"defect_id": str(defect.id), "error": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))
