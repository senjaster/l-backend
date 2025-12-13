"""Integration tests for StickerType API"""
import pytest
from fastapi.testclient import TestClient


def test_create_sticker_type(client: TestClient):
    """Test creating a new sticker type with temperature ranges"""
    sticker_type_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            },
            {
                "id": 2,
                "sticker_id": 1,
                "name": "High",
                "t_min": 51,
                "t_max": 100
            }
        ]
    }
    
    response = client.put("/sticker-type/1", json=sticker_type_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Sticker"
    assert len(data["temp_ranges"]) == 2


def test_get_sticker_type(client: TestClient):
    """Test retrieving a sticker type"""
    # First create
    sticker_type_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            }
        ]
    }
    client.put("/sticker-type/1", json=sticker_type_data)
    
    # Then get
    response = client.get("/sticker-type/1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Sticker"
    assert len(data["temp_ranges"]) == 1


def test_get_nonexistent_sticker_type(client: TestClient):
    """Test retrieving a non-existent sticker type"""
    response = client.get("/sticker-type/999")
    assert response.status_code == 404


def test_update_sticker_type(client: TestClient):
    """Test updating a sticker type"""
    # Create initial
    sticker_type_data = {
        "id": 1,
        "name": "Original Name",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            }
        ]
    }
    client.put("/sticker-type/1", json=sticker_type_data)
    
    # Update
    updated_data = {
        "id": 1,
        "name": "Updated Name",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low Updated",
                "t_min": 0,
                "t_max": 60
            }
        ]
    }
    response = client.put("/sticker-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["temp_ranges"][0]["name"] == "Low Updated"
    assert data["temp_ranges"][0]["t_max"] == 60


def test_sync_temp_ranges_add_new(client: TestClient):
    """Test adding new temperature ranges"""
    # Create with one range
    sticker_type_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            }
        ]
    }
    client.put("/sticker-type/1", json=sticker_type_data)
    
    # Update with additional range
    updated_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            },
            {
                "id": 2,
                "sticker_id": 1,
                "name": "High",
                "t_min": 51,
                "t_max": 100
            }
        ]
    }
    response = client.put("/sticker-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["temp_ranges"]) == 2


def test_sync_temp_ranges_remove(client: TestClient):
    """Test removing temperature ranges"""
    # Create with two ranges
    sticker_type_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            },
            {
                "id": 2,
                "sticker_id": 1,
                "name": "High",
                "t_min": 51,
                "t_max": 100
            }
        ]
    }
    client.put("/sticker-type/1", json=sticker_type_data)
    
    # Update with only one range
    updated_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": [
            {
                "id": 1,
                "sticker_id": 1,
                "name": "Low",
                "t_min": 0,
                "t_max": 50
            }
        ]
    }
    response = client.put("/sticker-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["temp_ranges"]) == 1
    assert data["temp_ranges"][0]["id"] == 1


def test_delete_sticker_type(client: TestClient):
    """Test logical deletion of sticker type"""
    # Create
    sticker_type_data = {
        "id": 1,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": []
    }
    client.put("/sticker-type/1", json=sticker_type_data)
    
    # Delete
    response = client.delete("/sticker-type/1")
    assert response.status_code == 204
    
    # Verify it's marked as deleted
    get_response = client.get("/sticker-type/1")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["is_deleted"] is True


def test_id_mismatch(client: TestClient):
    """Test ID mismatch in URL and body"""
    sticker_type_data = {
        "id": 2,
        "name": "Test Sticker",
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "temp_ranges": []
    }
    
    response = client.put("/sticker-type/1", json=sticker_type_data)
    assert response.status_code == 400