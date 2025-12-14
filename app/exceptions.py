"""Custom exception handlers"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
import asyncpg
from app.models import BaseError


async def asyncpg_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """Handle asyncpg database errors"""
    
    # Foreign key violation
    if isinstance(exc, asyncpg.ForeignKeyViolationError):
        error = BaseError(
            type="foreign_key_violation",
            message=str(exc).split('\n')[0]  # First line has the constraint name
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump()
        )
    
    # Unique constraint violation
    if isinstance(exc, asyncpg.UniqueViolationError):
        error = BaseError(
            type="unique_violation",
            message=str(exc).split('\n')[0]
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error.model_dump()
        )
    
    # Not null violation
    if isinstance(exc, asyncpg.NotNullViolationError):
        error = BaseError(
            type="not_null_violation",
            message=str(exc).split('\n')[0]
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump()
        )
    
    # Check constraint violation
    if isinstance(exc, asyncpg.CheckViolationError):
        error = BaseError(
            type="check_violation",
            message=str(exc).split('\n')[0]
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump()
        )
    
    # Generic database error
    error = BaseError(
        type="database_error",
        message="An unexpected database error occurred"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump()
    )