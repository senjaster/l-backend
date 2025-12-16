"""Inspector router"""
from fastapi import APIRouter, Depends
from app.models.inspector import InspectorListResponse
from app.repositories.inspector import InspectorRepository
from app.database import get_db_connection

router = APIRouter(prefix="/inspector", tags=["inspector"])
inspector_repo = InspectorRepository()


@router.get("/all", response_model=InspectorListResponse)
async def get_all_inspectors(conn=Depends(get_db_connection)):
    """Get all inspectors (read-only, without password_hash)"""
    inspectors = await inspector_repo.get_all(conn)
    return InspectorListResponse(items=inspectors)