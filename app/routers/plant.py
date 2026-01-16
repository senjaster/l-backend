"""Plant router - implements new API design principles"""

from uuid import UUID
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from app.constants import DEFAULT_MODIFIED_SINCE
from app.models.plant import Plant, PlantListResponse
from app.models.auth import TokenPayload
from app.repositories.plant import PlantRepository, ConcurrentModificationError
from app.database import get_db_connection
from app.dependencies.ownership import get_ownership_validator
from app.dependencies.auth import get_token_payload
from app.services.ownership_validator import OwnershipValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plant", tags=["plant"])
plant_repo = PlantRepository()


@router.get("/all", response_model=PlantListResponse)
async def get_all_plants(
    modified_since: datetime = Query(
        DEFAULT_MODIFIED_SINCE,
        description="Only return plants modified after this timestamp",
    ),
    conn=Depends(get_db_connection),
):
    """Get all plant IDs (lightweight list), optionally filtered by modification date"""
    return await plant_repo.get_all(conn, modified_since=modified_since)


@router.get("/by_id/{plant_id}", response_model=Plant)
async def get_plant_by_id(plant_id: UUID, conn=Depends(get_db_connection)):
    """Get specific plant with facilities and equipment IDs"""
    plant = await plant_repo.get_by_id(conn, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("", response_model=Plant)
async def upsert_plant(
    plant: Plant,
    force: bool = Query(
        default=False,
        description="If true, ignore server_modified_at and mark extra children as deleted",
    ),
    conn=Depends(get_db_connection),
    ownership_validator: OwnershipValidator = Depends(get_ownership_validator),
):
    """
    Create or replace plant with facilities.

    Rules:
    - force=false (default):
      - Validates server_modified_at for existing plants
      - Rejects if extra child facilities exist on server (409)
      - Ignores server_modified_at for new plants
    - force=true:
      - Ignores server_modified_at validation
      - Marks extra child facilities as deleted
    - Never allows "stealing" facilities from other plants
    - Pessimistic lock: Only the user who claimed the plant can modify it
    """
    try:
        async with conn.transaction():
            # Validate ownership before saving
            await ownership_validator.validate_plant_ownership(plant)
            result = await plant_repo.save(conn, plant, force=force)
        return result
    except ConcurrentModificationError as e:
        logger.warning(
            "Concurrent modification detected for plant",
            extra={
                "plant_id": str(plant.id),
                "conflict": e.conflict_error.model_dump(mode="json"),
            },
        )
        raise HTTPException(
            status_code=409, detail=e.conflict_error.model_dump(mode="json")
        )
    except ValueError as e:
        logger.warning(
            "Invalid plant data", extra={"plant_id": str(plant.id), "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/by_id/{plant_id}/claim", status_code=204)
async def claim_plant(
    plant_id: UUID,
    token_payload: TokenPayload = Depends(get_token_payload),
    conn=Depends(get_db_connection),
):
    """
    Claim plant for editing (user_id and device_id extracted from auth token).

    Allows claiming if:
    - Plant is not claimed
    - Plant is already claimed by the same user
    - Claim is stale (expired at 3:00 AM Moscow time)

    Returns 409 if plant is claimed by another user and claim is not stale.
    """
    async with conn.transaction():
        success = await plant_repo.claim(
            conn,
            plant_id,
            token_payload.dev,  # device_id from token
            token_payload.sub,  # user_id (inspector_id) from token
        )

    if success is None:
        raise HTTPException(status_code=404, detail="Plant not found")

    if not success:
        # Get plant info for better error message
        plant = await plant_repo.get_by_id(conn, plant_id)
        from app.models import ConflictError, ConflictDetail
        from datetime import datetime, timezone

        raise HTTPException(
            status_code=409,
            detail=ConflictError(
                message="Plant is claimed by another user and claim is not stale",
                server_modified_at=(
                    plant.server_modified_at if plant else datetime.now(timezone.utc)
                ),
                conflicts=[
                    ConflictDetail(
                        field="claimed_by_user_id",
                        message=f"Plant is claimed by user {plant.claimed_by_user_id if plant else 'unknown'} and claim has not expired yet",
                    )
                ],
            ).model_dump(mode="json"),
        )


@router.post("/by_id/{plant_id}/release", status_code=204)
async def release_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Release plant"""
    async with conn.transaction():
        success = await plant_repo.release(conn, plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")
