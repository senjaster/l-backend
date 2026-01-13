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
    conn = await asyncpg.connect(settings.get_database_url())
    try:
        # Run init_db.sql to set up the complete data structure
        with open('scripts/init_db.sql', 'r') as f:
            init_sql = f.read()
        await conn.execute(init_sql)
    finally:
        await conn.close()
    
    yield


@pytest_asyncio.fixture(scope="function")
async def seed_test_plant_and_facility(request):
    """Seed test plant and facility for each test function that needs them."""
    # Get plant_id if available
    plant_id = None
    facility_id = None
    
    if 'plant_id' in request.fixturenames:
        plant_id = request.getfixturevalue('plant_id')
    
    if 'facility_id' in request.fixturenames:
        facility_id = request.getfixturevalue('facility_id')
    
    # If we have a plant_id, seed the plant and facility
    if plant_id:
        conn = await asyncpg.connect(settings.get_database_url())
        try:
            # Insert test plant if not exists
            await conn.execute("""
                INSERT INTO lesiv.plant (id, name, server_modified_at)
                VALUES ($1, 'Test Plant', CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """, plant_id)
            
            # Insert test facility if not exists (only if facility_id is provided)
            if facility_id:
                await conn.execute("""
                    INSERT INTO lesiv.facility (id, plant_id, name)
                    VALUES ($1, $2, 'Test Facility')
                    ON CONFLICT (id) DO NOTHING
                """, facility_id, plant_id)
        finally:
            await conn.close()
    
    yield


@pytest_asyncio.fixture(scope="function")
async def seed_test_equipment(request):
    """Seed test equipment for each test function that needs it."""
    # Only run if equipment_id fixture is available
    if 'equipment_id' not in request.fixturenames:
        yield
        return
    
    # First ensure plant and facility exist
    if 'plant_id' in request.fixturenames and 'facility_id' in request.fixturenames:
        plant_id = request.getfixturevalue('plant_id')
        facility_id = request.getfixturevalue('facility_id')
        equipment_id = request.getfixturevalue('equipment_id')
        
        conn = await asyncpg.connect(settings.get_database_url())
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
            
            # Insert test equipment if not exists
            await conn.execute("""
                INSERT INTO lesiv.equipment (id, facility_id, parent_id, name, is_container, server_modified_at)
                VALUES ($1, $2, $2, 'Test Equipment', false, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            """, equipment_id, facility_id)
        finally:
            await conn.close()
    
    yield


@pytest.fixture(scope="function")
def client():
    """Create test client - FastAPI TestClient handles lifespan events."""
    with TestClient(app) as test_client:
        yield test_client