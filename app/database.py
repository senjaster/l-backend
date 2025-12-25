"""Database connection pool management"""
import asyncpg
from app.config import settings

db_pool: asyncpg.Pool = None


async def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
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


async def get_db_connection():
    """Dependency for getting database connection"""
    async with db_pool.acquire() as connection:
        yield connection