"""Authentication dependencies for FastAPI"""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
from app.models.inspector import Inspector
from app.models.auth import TokenPayload
from app.services.auth import AuthService
from app.database import get_db_connection
from app.config import settings
from datetime import datetime, timezone

security = HTTPBearer(auto_error=False)
auth_service = AuthService()


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> Inspector:
    """
    Dependency to get current authenticated user from JWT token.

    When auth is disabled (require_auth=False):
    - If a valid token is provided, returns the authenticated user
    - If no token is provided, returns anonymous user (id=-1)

    When auth is enabled (require_auth=True):
    - Requires a valid token, raises 401 if missing or invalid

    Raises:
        HTTPException: 401 if token is invalid or user not found (when auth is enabled)
    """
    # If credentials are provided, always try to validate them
    if credentials:
        token = credentials.credentials

        # Verify and decode token
        inspector_with_password = await auth_service.get_current_inspector(conn, token)

        if inspector_with_password is None:
            # Token is invalid
            if settings.require_auth:
                # Auth is enabled, reject invalid token
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                # Auth is disabled, fall through to return anonymous user
                pass
        else:
            # Token is valid, return the authenticated user
            return Inspector(
                id=inspector_with_password.id,
                username=inspector_with_password.username,
                full_name=inspector_with_password.full_name,
                is_deleted=False,  # Default value since it's not in the auth query
                server_modified_at=inspector_with_password.server_modified_at,
            )

    # No credentials provided or invalid token with auth disabled
    if settings.require_auth:
        # Auth is enabled, credentials are required
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Auth is disabled, return anonymous user
    return Inspector(
        id=-1,
        username="anonymous",
        full_name="Anonymous User",
        is_deleted=False,
        server_modified_at=datetime.now(timezone.utc),
    )


async def get_token_payload(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> TokenPayload:
    """
    Dependency to extract and validate token payload from JWT token.
    This provides access to both user_id (sub) and device_id (dev).

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = auth_service.verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
