"""Authentication middleware for global route protection"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth import AuthService
from app.config import settings
import app.database


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication on all routes except /auth"""
    
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()
        # Paths that don't require authentication
        self.public_paths = {
            "/",  # Health check
            "/docs",  # OpenAPI docs
            "/redoc",  # ReDoc
            "/openapi.json",  # OpenAPI schema
        }
    
    async def dispatch(self, request: Request, call_next):
        """Check authentication for all requests except public paths"""
        # If authentication is disabled, allow all requests
        if not settings.require_auth:
            return await call_next(request)
        
        path = request.url.path
        
        # Allow public paths
        if path in self.public_paths:
            return await call_next(request)
        
        # Allow all /auth routes (login, refresh)
        if path.startswith("/auth"):
            return await call_next(request)
        
        # All other routes require authentication
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check Bearer token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = parts[1]
        
        # Verify token and get inspector
        if app.database.db_pool is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Database connection not available"},
            )
        
        async with app.database.db_pool.acquire() as conn:
            inspector = await self.auth_service.get_current_inspector(conn, token)
        
        if not inspector:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Store inspector in request state for access in route handlers if needed
        request.state.current_user = inspector
        
        # Continue with the request
        return await call_next(request)