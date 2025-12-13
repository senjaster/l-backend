"""Pytest configuration and fixtures"""
import pytest
import pytest_asyncio
import asyncpg
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_test_inspector():
    """Seed test inspector once per test session using direct database connection."""
    # Create a direct connection to seed data (independent of app pool)
    conn = await asyncpg.connect(settings.database_url)
    try:
        # Insert test inspector if not exists
        await conn.execute("""
            INSERT INTO lesiv.inspector (id, full_name, username, password_hash, last_modified_at)
            VALUES (1, 'Test Inspector', 'test', 'hash', CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """)
    finally:
        await conn.close()
    
    yield


@pytest.fixture(scope="function")
def client():
    """Create test client - FastAPI TestClient handles lifespan events."""
    with TestClient(app) as test_client:
        yield test_client