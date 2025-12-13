"""Integration tests for Plant API - New API Design"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_create_plant(client: TestClient):
    """Test creating a new plant with facilities (server_modified_at ignored for new plants)"""
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Power Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,  # Ignored for new plants
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Building A"
            },
            {
                "id": str(facility_id_2),
                "name": "Building B"
            }
        ]
    }
    
    response = client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(plant_id)
    assert data["name"] == "Test Power Plant"
    assert len(data["facilities"]) == 2
    assert "server_modified_at" in data


def test_get_plant(client: TestClient):
    """Test retrieving a plant using new by_id endpoint"""
    # First create
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Main Building"
            }
        ]
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Then get
    response = client.get(f"/plant/by_id/{plant_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(plant_id)
    assert data["name"] == "Test Plant"
    assert len(data["facilities"]) == 1


def test_get_nonexistent_plant(client: TestClient):
    """Test retrieving a non-existent plant"""
    plant_id = uuid4()
    response = client.get(f"/plant/by_id/{plant_id}")
    assert response.status_code == 404


def test_get_all_plants(client: TestClient):
    """Test retrieving all plants using new /all endpoint"""
    # Create two plants
    plant_id_1 = uuid4()
    plant_id_2 = uuid4()
    
    plant_data_1 = {
        "name": "Plant One",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": []
    }
    
    plant_data_2 = {
        "name": "Plant Two",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": []
    }
    
    client.put(f"/plant/by_id/{plant_id_1}", json=plant_data_1)
    client.put(f"/plant/by_id/{plant_id_2}", json=plant_data_2)
    
    # Get all plants
    response = client.get("/plant/all")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data  # New response format
    assert len(data["items"]) >= 2
    
    # Check that our plants are in the list
    plant_ids = [p["id"] for p in data["items"]]
    assert str(plant_id_1) in plant_ids
    assert str(plant_id_2) in plant_ids


def test_update_plant_with_correct_timestamp(client: TestClient):
    """Test updating a plant with correct server_modified_at"""
    # Create initial
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Original Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Original Facility"
            }
        ]
    }
    create_response = client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    assert create_response.status_code == 200
    server_modified_at = create_response.json()["server_modified_at"]
    
    # Update with correct timestamp
    updated_data = {
        "name": "Updated Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": server_modified_at,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Updated Facility"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["facilities"][0]["name"] == "Updated Facility"
    assert data["server_modified_at"] != server_modified_at  # Should be updated


def test_concurrent_modification_detected(client: TestClient):
    """Test that concurrent modification is detected with 409 error"""
    # Create plant
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    create_response = client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    assert create_response.status_code == 200
    
    # Try to update with wrong timestamp
    wrong_data = {
        "name": "Updated Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": "2020-01-01T00:00:00Z",  # Wrong timestamp
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}", json=wrong_data)
    assert response.status_code == 409
    
    error_data = response.json()["detail"]
    assert error_data["error"] == "conflict"
    assert "modified by another client" in error_data["message"].lower()
    assert "server_modified_at" in error_data


def test_extra_facilities_rejected_without_force(client: TestClient):
    """Test that extra facilities on server are rejected when force=false"""
    # Create with two facilities
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            },
            {
                "id": str(facility_id_2),
                "name": "Facility 2"
            }
        ]
    }
    create_response = client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    assert create_response.status_code == 200
    server_modified_at = create_response.json()["server_modified_at"]
    
    # Try to update with only one facility (force=false)
    updated_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": server_modified_at,
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}?force=false", json=updated_data)
    assert response.status_code == 409
    
    error_data = response.json()["detail"]
    assert error_data["error"] == "conflict"
    assert "extra child facilities" in error_data["message"].lower()
    assert len(error_data["extra_child_ids"]) == 1
    assert str(facility_id_2) in error_data["extra_child_ids"]


def test_extra_facilities_deleted_with_force(client: TestClient):
    """Test that extra facilities are marked as deleted when force=true"""
    # Create with two facilities
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            },
            {
                "id": str(facility_id_2),
                "name": "Facility 2"
            }
        ]
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Update with only one facility (force=true)
    updated_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,  # Ignored when force=true
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}?force=true", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["facilities"]) == 2
    
    # Facility 1 should not be deleted
    facility_1 = next((f for f in data["facilities"] if f["id"] == str(facility_id_1)), None)
    assert facility_1 is not None
    assert facility_1["is_deleted"] is False
    
    # Facility 2 should be marked as deleted
    facility_2 = next((f for f in data["facilities"] if f["id"] == str(facility_id_2)), None)
    assert facility_2 is not None
    assert facility_2["is_deleted"] is True


def test_missing_timestamp_for_update(client: TestClient):
    """Test that missing server_modified_at is rejected for existing plants"""
    # Create plant
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Try to update without server_modified_at
    updated_data = {
        "name": "Updated Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,  # Missing timestamp
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}?force=false", json=updated_data)
    assert response.status_code == 409
    
    error_data = response.json()["detail"]
    assert "server_modified_at is required" in error_data["message"].lower()


def test_lock_plant(client: TestClient):
    """Test locking a plant using new by_id path"""
    # Create plant
    plant_id = uuid4()
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": []
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Lock plant
    device_id = uuid4()
    lock_request = {
        "device_id": str(device_id),
        "user_id": 1
    }
    response = client.post(f"/plant/by_id/{plant_id}/lock", json=lock_request)
    assert response.status_code == 204
    
    # Verify it's locked
    get_response = client.get(f"/plant/by_id/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["locked_by_device_id"] == str(device_id)
    assert data["locked_by_user_id"] == 1
    assert data["locked_at"] is not None


def test_unlock_plant(client: TestClient):
    """Test unlocking a plant using new by_id path"""
    # Create and lock plant
    plant_id = uuid4()
    device_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": str(device_id),
        "locked_by_user_id": 1,
        "locked_at": "2024-01-01T00:00:00Z",
        "server_modified_at": None,
        "facilities": []
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Unlock plant
    response = client.post(f"/plant/by_id/{plant_id}/unlock")
    assert response.status_code == 204
    
    # Verify it's unlocked
    get_response = client.get(f"/plant/by_id/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["locked_by_device_id"] is None
    assert data["locked_by_user_id"] is None
    assert data["locked_at"] is None


def test_facility_transfer_not_allowed(client: TestClient):
    """Test that transferring a facility from one plant to another is not allowed (never allow stealing)"""
    # Create first plant with a facility
    plant_id_1 = uuid4()
    facility_id = uuid4()
    
    plant_data_1 = {
        "name": "Plant One",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility A"
            }
        ]
    }
    client.put(f"/plant/by_id/{plant_id_1}", json=plant_data_1)
    
    # Try to create second plant and "steal" the facility
    plant_id_2 = uuid4()
    plant_data_2 = {
        "name": "Plant Two",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),  # Same facility ID from plant 1
                "name": "Facility A"
            }
        ]
    }
    
    # This should fail with 400 error (stealing never allowed, even with force=true)
    response = client.put(f"/plant/by_id/{plant_id_2}", json=plant_data_2)
    assert response.status_code == 400
    assert "cannot transfer" in response.json()["detail"].lower()


def test_force_mode_ignores_timestamp(client: TestClient):
    """Test that force=true ignores server_modified_at validation"""
    # Create plant
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": None,
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    client.put(f"/plant/by_id/{plant_id}", json=plant_data)
    
    # Update with wrong timestamp but force=true
    updated_data = {
        "name": "Updated Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "server_modified_at": "2020-01-01T00:00:00Z",  # Wrong timestamp
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/by_id/{plant_id}?force=true", json=updated_data)
    assert response.status_code == 200  # Should succeed with force=true
    
    data = response.json()
    assert data["name"] == "Updated Name"