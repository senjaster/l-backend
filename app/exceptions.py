"""Custom exception handlers"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
import asyncpg


async def asyncpg_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """Handle asyncpg database errors"""
    
    # Foreign key violation
    if isinstance(exc, asyncpg.ForeignKeyViolationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Foreign key constraint violation",
                "message": str(exc).split('\n')[0],  # First line has the constraint name
                "type": "foreign_key_violation"
            }
        )
    
    # Unique constraint violation
    if isinstance(exc, asyncpg.UniqueViolationError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Unique constraint violation",
                "message": str(exc).split('\n')[0],
                "type": "unique_violation"
            }
        )
    
    # Not null violation
    if isinstance(exc, asyncpg.NotNullViolationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Required field is missing",
                "message": str(exc).split('\n')[0],
                "type": "not_null_violation"
            }
        )
    
    # Check constraint violation
    if isinstance(exc, asyncpg.CheckViolationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Data validation failed",
                "message": str(exc).split('\n')[0],
                "type": "check_violation"
            }
        )
    
    # Generic database error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error",
            "message": "An unexpected database error occurred",
            "type": "database_error"
        }
    )