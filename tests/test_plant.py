"""Integration tests for Plant API"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_create_plant(client: TestClient):
    """Test creating a new plant with facilities"""
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Power Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
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
    
    response = client.put(f"/plant/{plant_id}", json=plant_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(plant_id)
    assert data["name"] == "Test Power Plant"
    assert len(data["facilities"]) == 2


def test_get_plant(client: TestClient):
    """Test retrieving a plant"""
    # First create
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Main Building"
            }
        ]
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Then get
    response = client.get(f"/plant/{plant_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(plant_id)
    assert data["name"] == "Test Plant"
    assert len(data["facilities"]) == 1


def test_get_nonexistent_plant(client: TestClient):
    """Test retrieving a non-existent plant"""
    plant_id = uuid4()
    response = client.get(f"/plant/{plant_id}")
    assert response.status_code == 404


def test_get_all_plants(client: TestClient):
    """Test retrieving all plants"""
    # Create two plants
    plant_id_1 = uuid4()
    plant_id_2 = uuid4()
    
    plant_data_1 = {
        "id": str(plant_id_1),
        "name": "Plant One",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": []
    }
    
    plant_data_2 = {
        "name": "Plant Two",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": []
    }
    
    client.put(f"/plant/{plant_id_1}", json=plant_data_1)
    client.put(f"/plant/{plant_id_2}", json=plant_data_2)
    
    # Get all plants
    response = client.get("/plant/plants")
    assert response.status_code == 200
    
    data = response.json()
    assert "plants" in data
    assert len(data["plants"]) >= 2
    
    # Check that our plants are in the list
    plant_ids = [p["id"] for p in data["plants"]]
    assert str(plant_id_1) in plant_ids
    assert str(plant_id_2) in plant_ids


def test_update_plant(client: TestClient):
    """Test updating a plant"""
    # Create initial
    plant_id = uuid4()
    facility_id = uuid4()
    
    plant_data = {
        "name": "Original Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Original Facility"
            }
        ]
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Update
    updated_data = {
        "name": "Updated Name",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-02T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id),
                "name": "Updated Facility"
            }
        ]
    }
    response = client.put(f"/plant/{plant_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["facilities"][0]["name"] == "Updated Facility"


def test_sync_facilities_add_new(client: TestClient):
    """Test adding new facilities"""
    # Create with one facility
    plant_id = uuid4()
    facility_id_1 = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            }
        ]
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Update with additional facility
    facility_id_2 = uuid4()
    updated_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
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
    response = client.put(f"/plant/{plant_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["facilities"]) == 2


def test_sync_facilities_remove(client: TestClient):
    """Test removing facilities (logical deletion)"""
    # Create with two facilities
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
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
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Update with only one facility
    updated_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/{plant_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    # Should have 2 facilities (including the deleted one)
    assert len(data["facilities"]) == 2
    
    # Facility 1 should not be deleted
    facility_1 = next((f for f in data["facilities"] if f["id"] == str(facility_id_1)), None)
    assert facility_1 is not None
    assert facility_1["is_deleted"] is False
    
    # Facility 2 should be marked as deleted
    facility_2 = next((f for f in data["facilities"] if f["id"] == str(facility_id_2)), None)
    assert facility_2 is not None
    assert facility_2["is_deleted"] is True


def test_delete_plant(client: TestClient):
    """Test logical deletion of plant"""
    # Create
    plant_id = uuid4()
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "is_deleted": False,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": []
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Delete
    response = client.delete(f"/plant/{plant_id}")
    assert response.status_code == 204
    
    # Verify it's marked as deleted
    get_response = client.get(f"/plant/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["is_deleted"] is True


def test_lock_plant(client: TestClient):
    """Test locking a plant"""
    # Create plant
    plant_id = uuid4()
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": []
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Lock plant
    device_id = uuid4()
    lock_request = {
        "device_id": str(device_id),
        "user_id": 1
    }
    response = client.post(f"/plant/{plant_id}/lock", json=lock_request)
    assert response.status_code == 204
    
    # Verify it's locked
    get_response = client.get(f"/plant/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["locked_by_device_id"] == str(device_id)
    assert data["locked_by_user_id"] == 1
    assert data["locked_at"] is not None


def test_unlock_plant(client: TestClient):
    """Test unlocking a plant"""
    # Create and lock plant
    plant_id = uuid4()
    device_id = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": str(device_id),
        "locked_by_user_id": 1,
        "locked_at": "2024-01-01T00:00:00Z",
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": []
    }
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Unlock plant
    response = client.post(f"/plant/{plant_id}/unlock")
    assert response.status_code == 204
    
    # Verify it's unlocked
    get_response = client.get(f"/plant/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["locked_by_device_id"] is None
    assert data["locked_by_user_id"] is None
    assert data["locked_at"] is None


def test_facility_transfer_not_allowed(client: TestClient):
    """Test that transferring a facility from one plant to another is not allowed"""
    # Create first plant with a facility
    plant_id_1 = uuid4()
    facility_id = uuid4()
    
    plant_data_1 = {
        "id": str(plant_id_1),
        "name": "Plant One",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id),
                "plant_id": str(plant_id_1),
                "name": "Facility A"
            }
        ]
    }
    client.put(f"/plant/{plant_id_1}", json=plant_data_1)
    
    # Try to create second plant and "steal" the facility
    plant_id_2 = uuid4()
    plant_data_2 = {
        "name": "Plant Two",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id),  # Same facility ID from plant 1
                "plant_id": str(plant_id_2),  # But claiming it belongs to plant 2
                "name": "Facility A"
            }
        ]
    }
    
    # This should fail with 400 error
    response = client.put(f"/plant/{plant_id_2}", json=plant_data_2)
    assert response.status_code == 400
    assert "belongs to another plant" in response.json()["detail"].lower()


def test_facility_logical_deletion(client: TestClient):
    """Test that removing a facility marks it as deleted, not physically deletes it"""
    # Create plant with two facilities
    plant_id = uuid4()
    facility_id_1 = uuid4()
    facility_id_2 = uuid4()
    
    plant_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
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
    client.put(f"/plant/{plant_id}", json=plant_data)
    
    # Update plant, removing facility 2
    updated_data = {
        "name": "Test Plant",
        "locked_by_device_id": None,
        "locked_by_user_id": None,
        "locked_at": None,
        "last_modified_at": "2024-01-01T00:00:00Z",
        "facilities": [
            {
                "id": str(facility_id_1),
                "name": "Facility 1"
            }
        ]
    }
    response = client.put(f"/plant/{plant_id}", json=updated_data)
    assert response.status_code == 200
    
    # Get the plant again - facility 2 should still exist but marked as deleted
    get_response = client.get(f"/plant/{plant_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    
    # Should have 2 facilities total (including deleted one)
    assert len(data["facilities"]) == 2
    
    # Find facility 2 and verify it's marked as deleted
    facility_2 = next((f for f in data["facilities"] if f["id"] == str(facility_id_2)), None)
    assert facility_2 is not None, "Facility 2 should still exist in database"
    assert facility_2["is_deleted"] is True, "Facility 2 should be marked as deleted"
    
    # Facility 1 should not be deleted
    facility_1 = next((f for f in data["facilities"] if f["id"] == str(facility_id_1)), None)
    assert facility_1 is not None
    assert facility_1["is_deleted"] is False