"""Inspector router"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.inspector import Inspector
from app.repositories.inspector import InspectorRepository
from app.database import get_db_connection

router = APIRouter(prefix="/inspector", tags=["inspector"])
inspector_repo = InspectorRepository()


@router.get("/{inspector_id}", response_model=Inspector)
async def get_inspector(inspector_id: int, conn=Depends(get_db_connection)):
    """Get inspector by ID (read-only)"""
    inspector = await inspector_repo.get_by_id(conn, inspector_id)
    if not inspector:
        raise HTTPException(status_code=404, detail="Inspector not found")
    return inspector