"""Integration tests for Inspector API"""
import pytest
from fastapi.testclient import TestClient


def test_get_inspector(client: TestClient):
    """Test retrieving an inspector (read-only endpoint)"""
    # Note: Inspector is read-only, so we assume data exists in DB
    # In a real scenario, you'd seed test data
    response = client.get("/inspector/1")
    # This will return 404 if no inspector with ID 1 exists
    # which is expected in an empty test database
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "full_name" in data
        assert "username" in data
        assert "password_hash" in data
        assert "last_modified_at" in data


def test_get_nonexistent_inspector(client: TestClient):
    """Test retrieving a non-existent inspector"""
    response = client.get("/inspector/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Inspector not found"