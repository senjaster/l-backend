"""Integration tests for Equipment API"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from copy import deepcopy

PUT_BODY_TEMPLATE = {
        "name": "Test Motor",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": 50,
        "server_modified_at": "2024-01-01T10:00:00Z",
        "control_points": [
            {
                "control_point_type": "БКС",
                "point_count": 30,
                "sticker_count": 25,
                "sticker_type_id": None,
                "t_max": 90,
                "t_excess": 40,
                "is_deleted": False
            },
        ],
        "defects": [
            {
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

@pytest.fixture
def equipment_id():
    return uuid4()


@pytest.fixture
def plant_id():
    return uuid4()


@pytest.fixture
def facility_id():
    return uuid4()


@pytest.fixture
def control_point_id_1():
    return uuid4()


@pytest.fixture
def defect_id_1():
    return uuid4()

@pytest.fixture
def equipment_data(equipment_id, plant_id, facility_id, control_point_id_1, defect_id_1):
    data = deepcopy(PUT_BODY_TEMPLATE)
    data["id"] = str(equipment_id)
    data["plant_id"] = str(plant_id)
    data["parent_id"] = str(facility_id)
    data["control_points"][0]["id"] = str(control_point_id_1)
    data["defects"][0]["id"] = str(defect_id_1)
    return data

def test_create_equipment(client: TestClient, equipment_data, equipment_id, plant_id, facility_id):
    """Test creating a new equipment with control points and defects"""
    
    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(equipment_id)
    assert data["name"] == "Test Motor"
    assert data["plant_id"] == str(plant_id)
    assert data["parent_id"] == str(facility_id)
    assert len(data["control_points"]) == 1
    assert len(data["defects"]) == 1


def test_get_equipment(client: TestClient, equipment_data, equipment_id):
    """Test retrieving equipment"""
    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    # Then get
    response = client.get(f"/equipment/by_id/{equipment_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(equipment_id)
    assert data["name"] == "Test Motor"
    assert len(data["control_points"]) == 1


def test_get_nonexistent_equipment(client: TestClient):
    """Test retrieving a non-existent equipment"""
    equipment_id = uuid4()
    response = client.get(f"/equipment/by_id/{equipment_id}")
    assert response.status_code == 404


def test_update_equipment(client: TestClient, equipment_data):
    """Test updating equipment"""
    
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]
    
    equipment_data["server_modified_at"] = server_modified_at
    equipment_data["name"] = "Updated Name"
    equipment_data["control_points"][0]["point_count"] = 15
    equipment_data["control_points"][0]["is_deleted"] = True
    equipment_data["defects"][0]["is_deleted"] = True

    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["control_points"][0]["point_count"] == 15
    assert data["control_points"][0]["is_deleted"] == True
    assert data["defects"][0]["is_deleted"] == True

def test_sync_control_points_add_new(client: TestClient, equipment_data):
    """Test adding new control points"""
    
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    
    # Update with additional control point
    control_point_id_2 = uuid4()

    equipment_data["control_points"].append(
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
        )
    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["control_points"]) == 2


def test_sync_control_points_reject_missing_child(client: TestClient, equipment_data):
    """Test marking control points as deleted explicitly"""
    control_point_id_2 = uuid4()
    equipment_data["control_points"].append(
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
    )
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    
    del equipment_data["control_points"][0]

    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 409

def test_sync_control_points_force_update(client: TestClient, equipment_data):
    """Test marking control points as deleted explicitly"""
    control_point_id_2 = uuid4()
    equipment_data["control_points"].append(
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
    )
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    
    del equipment_data["control_points"][0]

    response = client.put(f"/equipment?force=true", json=equipment_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["control_points"]) == 2
    # This might be flaky:
    assert data["control_points"][0]["is_deleted"] == True
    assert data["control_points"][1]["is_deleted"] == False

def test_sync_defects_add_new(client: TestClient, equipment_data):
    """Test adding new defects"""
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    
    # Update with additional defect
    defect_id_2 = uuid4()
    equipment_data["defects"].append(
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
    )
    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["defects"]) == 2

def test_sync_defects_reject_missing_child(client: TestClient, equipment_data):
    """Test adding new defects"""
    
    # Update with additional defect
    defect_id_2 = uuid4()
    equipment_data["defects"].append(
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
    )
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at

    del equipment_data["defects"][0]

    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 409

def test_sync_defects_force_update(client: TestClient, equipment_data, defect_id_1):
    """Test adding new defects"""
    
    # Update with additional defect
    defect_id_2 = uuid4()
    equipment_data["defects"].append(
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
    )
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at

    del equipment_data["defects"][0]

    response = client.put(f"/equipment?force=true", json=equipment_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["defects"]) == 2
    for defect in data["defects"]:
        is_deleted = defect["is_deleted"]
        id = defect["id"]
        assert (not is_deleted and id == str(defect_id_2)) or (is_deleted and id == str(defect_id_1)) 



def test_sync_defects_resolve(client: TestClient, equipment_data):
    """Test resolving defects"""
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    equipment_data["defects"][0]["resolved_at"] = "2024-01-03T10:00:00Z"
    equipment_data["defects"][0]["status"] = "RESOLVED"

    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["defects"]) == 1
    assert data["defects"][0]["status"] == "RESOLVED"
    assert data["defects"][0]["resolved_at"] is not None


def test_delete_equipment(client: TestClient, equipment_data, equipment_id):
    """Test logical deletion of equipment"""
    create_response = client.put(f"/equipment", json=equipment_data)
    server_modified_at = create_response.json()["server_modified_at"]  
    equipment_data["server_modified_at"] = server_modified_at
    equipment_data["is_deleted"] = True

    response = client.put(f"/equipment", json=equipment_data)
    assert response.status_code == 200    
    
    # Verify it's marked as deleted
    get_response = client.get(f"/equipment/by_id/{equipment_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["is_deleted"] is True

def test_defect_transfer_not_allowed(client: TestClient, equipment_data, equipment_id, plant_id, facility_id):
    """Test that transferring a defect from one equipment to another is not allowed"""
    create_response = client.put(f"/equipment", json=equipment_data)
    assert create_response.status_code == 200

    equipment_id2 = uuid4()

    equipment_data2 = {
        "id": str(equipment_id2),
        "plant_id": str(plant_id), 
        "facility_id": str(facility_id),
        "name": "Test Motor 2",
        "is_container": False,
        "equipment_type_id": None,
        "estimated_point_count": 50,
        "server_modified_at": "2024-01-01T10:00:00Z",
        "control_points": [],
        "defects": equipment_data['defects']  # Transfer 
    }

    response = client.put(f"/equipment", json=equipment_data2)
    assert response.status_code == 400
    assert "cannot transfer" in response.json()["detail"].lower()