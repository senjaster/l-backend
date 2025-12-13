"""Integration tests for Equipment API"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


def test_create_equipment(client: TestClient):
    """Test creating a new equipment with control points and defects"""
    equipment_id = uuid4()
    plant_id = uuid4()
    facility_id = uuid4()
    control_point_id_1 = uuid4()
    control_point_id_2 = uuid4()
    defect_id = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": str(facility_id),
        "name": "Test Motor",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": 50,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 30,
                "sticker_count": 25,
                "sticker_type_id": None,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            },
            {
                "id": str(control_point_id_2),
                "control_point_type": "Подшипник",
                "point_count": 20,
                "sticker_count": 15,
                "sticker_type_id": None,
                "t_max": 80,
                "t_excess": 35,
                "is_deleted": False
            }
        ],
        "defects": [
            {
                "id": str(defect_id),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    
    response = client.put(f"/equipment/{equipment_id}", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(equipment_id)
    assert data["name"] == "Test Motor"
    assert data["plant_id"] == str(plant_id)
    assert data["parent_id"] == str(facility_id)
    assert len(data["control_points"]) == 2
    assert len(data["defects"]) == 1


def test_get_equipment(client: TestClient):
    """Test retrieving equipment"""
    # First create
    equipment_id = uuid4()
    plant_id = uuid4()
    control_point_id = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Then get
    response = client.get(f"/equipment/{equipment_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(equipment_id)
    assert data["name"] == "Test Equipment"
    assert len(data["control_points"]) == 1


def test_get_nonexistent_equipment(client: TestClient):
    """Test retrieving a non-existent equipment"""
    equipment_id = uuid4()
    response = client.get(f"/equipment/{equipment_id}")
    assert response.status_code == 404


def test_update_equipment(client: TestClient):
    """Test updating equipment"""
    # Create initial
    equipment_id = uuid4()
    plant_id = uuid4()
    control_point_id = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Original Name",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Update
    updated_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Updated Name",
        "is_container": False,
        "equipment_type_id": 1,
        "estimated_point_count": 50,
        "control_points": [
            {
                "id": str(control_point_id),
                "control_point_type": "БКС",
                "point_count": 15,
                "sticker_count": 12,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    response = client.put(f"/equipment/{equipment_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["equipment_type_id"] == 1
    assert data["control_points"][0]["point_count"] == 15


def test_sync_control_points_add_new(client: TestClient):
    """Test adding new control points"""
    # Create with one control point
    equipment_id = uuid4()
    plant_id = uuid4()
    control_point_id_1 = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Update with additional control point
    control_point_id_2 = uuid4()
    updated_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            },
            {
                "id": str(control_point_id_2),
                "control_point_type": "Подшипник",
                "point_count": 5,
                "sticker_count": 4,
                "sticker_type_id": None,
                "t_max": 80,
                "t_excess": 35,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    response = client.put(f"/equipment/{equipment_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["control_points"]) == 2


def test_sync_control_points_mark_deleted(client: TestClient):
    """Test marking control points as deleted explicitly"""
    # Create with two control points
    equipment_id = uuid4()
    plant_id = uuid4()
    control_point_id_1 = uuid4()
    control_point_id_2 = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            },
            {
                "id": str(control_point_id_2),
                "control_point_type": "Подшипник",
                "point_count": 5,
                "sticker_count": 4,
                "sticker_type_id": None,
                "t_max": 80,
                "t_excess": 35,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Update with second control point marked as deleted
    updated_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": 1,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            },
            {
                "id": str(control_point_id_2),
                "control_point_type": "Подшипник",
                "point_count": 5,
                "sticker_count": 4,
                "sticker_type_id": None,
                "t_max": 80,
                "t_excess": 35,
                "is_deleted": True  # Explicitly mark as deleted
            }
        ],
        "defects": []
    }
    response = client.put(f"/equipment/{equipment_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    # Should have 2 control points
    assert len(data["control_points"]) == 2
    
    # Control point 1 should not be deleted
    cp_1 = next((cp for cp in data["control_points"] if cp["id"] == str(control_point_id_1)), None)
    assert cp_1 is not None
    assert cp_1["is_deleted"] is False
    
    # Control point 2 should be marked as deleted
    cp_2 = next((cp for cp in data["control_points"] if cp["id"] == str(control_point_id_2)), None)
    assert cp_2 is not None
    assert cp_2["is_deleted"] is True


def test_sync_defects_add_new(client: TestClient):
    """Test adding new defects"""
    # Create with one defect
    equipment_id = uuid4()
    plant_id = uuid4()
    defect_id_1 = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id_1),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Update with additional defect
    defect_id_2 = uuid4()
    updated_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id_1),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            },
            {
                "id": str(defect_id_2),
                "unit_name": "нижний БКС фаза А",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-02T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    response = client.put(f"/equipment/{equipment_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["defects"]) == 2


def test_sync_defects_resolve(client: TestClient):
    """Test resolving defects"""
    # Create with one defect
    equipment_id = uuid4()
    plant_id = uuid4()
    defect_id = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Update defect to resolved
    updated_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": "2024-01-05T10:00:00Z",
                "status": "RESOLVED",
                "is_deleted": False
            }
        ]
    }
    response = client.put(f"/equipment/{equipment_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["defects"]) == 1
    assert data["defects"][0]["status"] == "RESOLVED"
    assert data["defects"][0]["resolved_at"] is not None


def test_delete_equipment(client: TestClient):
    """Test logical deletion of equipment"""
    # Create
    equipment_id = uuid4()
    plant_id = uuid4()
    
    equipment_data = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Test Equipment",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": []
    }
    client.put(f"/equipment/{equipment_id}", json=equipment_data)
    
    # Delete
    response = client.delete(f"/equipment/{equipment_id}")
    assert response.status_code == 204
    
    # Verify it's marked as deleted
    get_response = client.get(f"/equipment/{equipment_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["is_deleted"] is True


def test_control_point_same_type_different_equipment(client: TestClient):
    """Test that different equipment can have control points of the same type"""
    # Create first equipment with a control point
    equipment_id_1 = uuid4()
    plant_id = uuid4()
    control_point_id_1 = uuid4()
    
    equipment_data_1 = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Equipment One",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_1),
                "control_point_type": "БКС",
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": None,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    response1 = client.put(f"/equipment/{equipment_id_1}", json=equipment_data_1)
    assert response1.status_code == 200
    
    # Create second equipment with same control point type (but different ID)
    equipment_id_2 = uuid4()
    control_point_id_2 = uuid4()
    equipment_data_2 = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Equipment Two",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [
            {
                "id": str(control_point_id_2),  # Different ID
                "control_point_type": "БКС",  # Same type - this is allowed
                "point_count": 10,
                "sticker_count": 8,
                "sticker_type_id": None,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            }
        ],
        "defects": []
    }
    
    # This should succeed - different equipment can have same control point types
    response2 = client.put(f"/equipment/{equipment_id_2}", json=equipment_data_2)
    assert response2.status_code == 200


def test_defect_transfer_not_allowed(client: TestClient):
    """Test that transferring a defect from one equipment to another is not allowed"""
    # Create first equipment with a defect
    equipment_id_1 = uuid4()
    plant_id = uuid4()
    defect_id = uuid4()
    
    equipment_data_1 = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Equipment One",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id),
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    client.put(f"/equipment/{equipment_id_1}", json=equipment_data_1)
    
    # Try to create second equipment and "steal" the defect
    equipment_id_2 = uuid4()
    equipment_data_2 = {
        "plant_id": str(plant_id),
        "parent_id": None,
        "name": "Equipment Two",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": None,
        "control_points": [],
        "defects": [
            {
                "id": str(defect_id),  # Same defect ID from equipment 1
                "unit_name": "верхний БКС фаза В",
                "t_max": 90,
                "t_excess": 40,
                "detected_at": "2024-01-01T10:00:00Z",
                "resolved_at": None,
                "status": "DETECTED",
                "is_deleted": False
            }
        ]
    }
    
    # This should fail with 400 error
    response = client.put(f"/equipment/{equipment_id_2}", json=equipment_data_2)
    assert response.status_code == 400
    assert "belongs to another equipment" in response.json()["detail"].lower()