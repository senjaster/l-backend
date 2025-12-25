"""Database connection pool management"""
import asyncpg
from typing import Optional
from app.config import settings

db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            dsn=settings.get_database_url(),
            min_size=5,
            max_size=20,
            command_timeout=60
        )


async def close_db_pool():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None


async def get_db_connection():
    """
    Dependency for getting database connection.
    
    In serverless environments where lifespan is disabled,
    this will initialize the pool on first request if needed.
    """
    global db_pool
    
    # Initialize pool if not already initialized (for serverless environments)
    if db_pool is None:
        await init_db_pool()
    
    # At this point db_pool should be initialized
    if db_pool is not None:
        async with db_pool.acquire() as connection:
            yield connection