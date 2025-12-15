"""Authentication router"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.models.auth import LoginRequest, LoginResponse, RefreshRequest, RefreshResponse
from app.services.auth import AuthService
from app.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]
):
    """
    Login endpoint - authenticate user and return access and refresh tokens.
    
    Args:
        request: Login credentials (username, password, device_id)
        conn: Database connection
    
    Returns:
        LoginResponse with access_token and refresh_token
    
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    result = await auth_service.login(
        conn,
        username=request.username,
        password=request.password,
        device_id=request.device_id
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: RefreshRequest,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]
):
    """
    Refresh endpoint - rotate refresh token and return new access and refresh tokens.
    
    Implements:
    - Token rotation: old token is revoked, new token is issued
    - Theft detection: if revoked token is reused, entire chain is revoked
    - Grace window: allows token reuse within a small time window for race conditions
    
    Args:
        request: Refresh token request
        conn: Database connection
    
    Returns:
        RefreshResponse with new access_token and refresh_token
    
    Raises:
        HTTPException: 401 if refresh token is invalid, expired, or revoked
    """
    result = await auth_service.refresh(
        conn,
        refresh_token_string=request.refresh_token
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result