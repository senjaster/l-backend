"""Wrapper to make sync objects work with async syntax"""
from typing import Any
from contextlib import asynccontextmanager


class AsyncIteratorWrapper:
    """Wraps a sync iterator to work with 'async for'"""
    
    def __init__(self, sync_iterator):
        self._iterator = iter(sync_iterator)
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration


class AsyncWrapper:
    """
    Wraps a sync object to make its methods callable with async/await syntax.
    
    This allows using sync database drivers (like psycopg2) with async code,
    which is useful in serverless environments where:
    - Event loops are created per-request anyway (no concurrency benefit)
    - Sync connection pools persist across warm invocations
    
    Usage:
        sync_queries = aiosql.from_path("queries.sql", "psycopg2")
        async_queries = AsyncWrapper(sync_queries)
        
        # Now you can use await even though underlying call is sync
        result = await async_queries.get_by_id(conn, id=123)
        
        # Also works with async for
        async for row in async_queries.get_all(conn):
            process(row)
    """
    
    def __init__(self, wrapped_obj: Any):
        self._wrapped = wrapped_obj
    
    def __getattr__(self, name: str):
        """Intercept attribute access and wrap methods to be awaitable"""
        attr = getattr(self._wrapped, name)
        
        if callable(attr):
            async def async_wrapper(*args, **kwargs):
                # Call the sync method directly
                result = attr(*args, **kwargs)
                
                # If result is an iterator/generator, wrap it for async iteration
                if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict, list, tuple)):
                    return AsyncIteratorWrapper(result)
                
                return result
            
            return async_wrapper
        
        return attr


class AsyncConnectionWrapper:
    """
    Wraps a sync database connection to provide async-compatible transaction() method.
    
    This is specifically for psycopg2 connections to work with code that expects
    asyncpg-style async context manager transactions.
    """
    
    def __init__(self, sync_conn):
        self._conn = sync_conn
    
    def __getattr__(self, name: str):
        """Forward all other attributes to the wrapped connection"""
        return getattr(self._conn, name)
    
    @asynccontextmanager
    async def transaction(self):
        """
        Provide async context manager for transactions on sync connection.
        
        Usage:
            async with conn.transaction():
                # do database operations
        """
        # For psycopg2, transactions are implicit - just need to commit/rollback
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
