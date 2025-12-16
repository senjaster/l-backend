"""Pytest configuration and fixtures"""
import pytest
import pytest_asyncio
import asyncpg
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

# Disable authentication for all tests
settings.require_auth = False


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_test_data():
    """Seed test data once per test session using direct database connection."""
    # Create a direct connection to seed data (independent of app pool)
    conn = await asyncpg.connect(settings.database_url)
    try:
        # Load and execute sticker types seed file
        with open('tests/seed_data.sql', 'r') as f:
            seed_sql = f.read()
        await conn.execute(seed_sql)
    finally:
        await conn.close()
    
    yield


@pytest_asyncio.fixture(scope="function")
async def seed_test_plant_and_facility(request):
    """Seed test plant and facility for each test function that needs them."""
    # Only run if plant_id and facility_id fixtures are available
    if 'plant_id' not in request.fixturenames or 'facility_id' not in request.fixturenames:
        yield
        return
    
    plant_id = request.getfixturevalue('plant_id')
    facility_id = request.getfixturevalue('facility_id')
    
    conn = await asyncpg.connect(settings.database_url)
    try:
        # Insert test plant if not exists
        await conn.execute("""
            INSERT INTO lesiv.plant (id, name, server_modified_at)
            VALUES ($1, 'Test Plant', CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """, plant_id)
        
        # Insert test facility if not exists
        await conn.execute("""
            INSERT INTO lesiv.facility (id, plant_id, name)
            VALUES ($1, $2, 'Test Facility')
            ON CONFLICT (id) DO NOTHING
        """, facility_id, plant_id)
    finally:
        await conn.close()
    
    yield


@pytest.fixture(scope="function")
def client():
    """Create test client - FastAPI TestClient handles lifespan events."""
    with TestClient(app) as test_client:
        yield test_client