"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="function")
def client():
    """Create test client - FastAPI TestClient handles lifespan events"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Clean test database before each test"""
    # This will run before each test
    # Note: In a real scenario, you'd want to use a test database
    # For now, we'll rely on unique IDs in tests
    yield
    # Cleanup after test if needed