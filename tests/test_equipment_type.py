"""Integration tests for EquipmentType API"""
import pytest
from fastapi.testclient import TestClient


def test_create_equipment_type(client: TestClient):
    """Test creating a new equipment type with control point templates"""
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            },
            {
                "id": 2,
                "equipment_type_id": 1,
                "name": "Winding",
                "short_name": "WND",
                "t_max": 100,
                "t_excess": 50,
                "default_sticker_id": None
            }
        ]
    }
    
    response = client.put("/equipment-type/1", json=equipment_type_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Motor"
    assert len(data["control_point_templates"]) == 2


def test_get_equipment_type(client: TestClient):
    """Test retrieving an equipment type"""
    # First create
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            }
        ]
    }
    client.put("/equipment-type/1", json=equipment_type_data)
    
    # Then get
    response = client.get("/equipment-type/1")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Motor"
    assert len(data["control_point_templates"]) == 1


def test_get_nonexistent_equipment_type(client: TestClient):
    """Test retrieving a non-existent equipment type"""
    response = client.get("/equipment-type/999")
    assert response.status_code == 404


def test_update_equipment_type(client: TestClient):
    """Test updating an equipment type"""
    # Create initial
    equipment_type_data = {
        "id": 1,
        "name": "Original Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            }
        ]
    }
    client.put("/equipment-type/1", json=equipment_type_data)
    
    # Update
    updated_data = {
        "id": 1,
        "name": "Updated Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing Updated",
                "short_name": "BRG",
                "t_max": 90,
                "t_excess": 45,
                "default_sticker_id": None
            }
        ]
    }
    response = client.put("/equipment-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Motor"
    assert data["control_point_templates"][0]["name"] == "Bearing Updated"
    assert data["control_point_templates"][0]["t_max"] == 90


def test_sync_templates_add_new(client: TestClient):
    """Test adding new control point templates"""
    # Create with one template
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            }
        ]
    }
    client.put("/equipment-type/1", json=equipment_type_data)
    
    # Update with additional template
    updated_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            },
            {
                "id": 2,
                "equipment_type_id": 1,
                "name": "Winding",
                "short_name": "WND",
                "t_max": 100,
                "t_excess": 50,
                "default_sticker_id": None
            }
        ]
    }
    response = client.put("/equipment-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["control_point_templates"]) == 2


def test_sync_templates_remove(client: TestClient):
    """Test removing control point templates"""
    # Create with two templates
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            },
            {
                "id": 2,
                "equipment_type_id": 1,
                "name": "Winding",
                "short_name": "WND",
                "t_max": 100,
                "t_excess": 50,
                "default_sticker_id": None
            }
        ]
    }
    client.put("/equipment-type/1", json=equipment_type_data)
    
    # Update with only one template
    updated_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": None
            }
        ]
    }
    response = client.put("/equipment-type/1", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["control_point_templates"]) == 1
    assert data["control_point_templates"][0]["id"] == 1


def test_delete_equipment_type(client: TestClient):
    """Test deletion of equipment type"""
    # Create
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": []
    }
    client.put("/equipment-type/1", json=equipment_type_data)
    
    # Delete
    response = client.delete("/equipment-type/1")
    assert response.status_code == 204
    
    # Verify it's deleted (should return 404)
    get_response = client.get("/equipment-type/1")
    assert get_response.status_code == 404


def test_id_mismatch(client: TestClient):
    """Test ID mismatch in URL and body"""
    equipment_type_data = {
        "id": 2,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": []
    }
    
    response = client.put("/equipment-type/1", json=equipment_type_data)
    assert response.status_code == 400


def test_template_with_sticker_reference(client: TestClient):
    """Test control point template with sticker type reference"""
    equipment_type_data = {
        "id": 1,
        "name": "Test Motor",
        "server_modified_at": "2024-01-01T00:00:00Z",
        "control_point_templates": [
            {
                "id": 1,
                "equipment_type_id": 1,
                "name": "Bearing",
                "short_name": "BRG",
                "t_max": 80,
                "t_excess": 40,
                "default_sticker_id": 1
            }
        ]
    }
    
    response = client.put("/equipment-type/1", json=equipment_type_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["control_point_templates"][0]["default_sticker_id"] == 1