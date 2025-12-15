"""Authentication dependencies for FastAPI"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
from app.models.inspector import Inspector
from app.services.auth import AuthService
from app.database import get_db_connection

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]
) -> Inspector:
    """
    Dependency to get current authenticated user from JWT token.
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify and decode token
    inspector = await auth_service.get_current_inspector(conn, token)
    
    if inspector is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return inspector