"""Integration tests for EquipmentType API"""
import pytest
from fastapi.testclient import TestClient


def test_get_all_equipment_types(client: TestClient):
    """Test retrieving all equipment types"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    items = data["items"]
    
    # Should have 3 equipment types
    assert len(items) == 3
    
    # Verify structure of first item
    assert all(key in items[0] for key in ["id", "name", "server_modified_at", "control_point_templates"])


def test_equipment_type_with_templates(client: TestClient):
    """Test that equipment types include their control point templates"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Find equipment type 1
    motor = next((item for item in items if item["id"] == 1), None)
    assert motor is not None
    assert motor["name"] in ["Electric Motor", "Test Motor"]  # Allow both seeded and test data
    
    # Should have 2 control point templates
    assert len(motor["control_point_templates"]) == 2
    
    # Verify template structure
    template = motor["control_point_templates"][0]
    assert all(key in template for key in ["id", "equipment_type_id", "name", "short_name", "t_max", "t_excess", "default_sticker_id"])


def test_equipment_type_template_values(client: TestClient):
    """Test control point template values are correct"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Find equipment type 1 (Electric Motor)
    motor = next((item for item in items if item["id"] == 1), None)
    assert motor is not None
    
    # Verify templates
    templates = motor["control_point_templates"]
    assert len(templates) == 2
    
    # Check Bearing template
    bearing = next((t for t in templates if t["name"] == "Bearing"), None)
    assert bearing is not None
    assert bearing["short_name"] == "BRG"
    assert bearing["t_max"] == 80
    assert bearing["t_excess"] == 40
    assert bearing["default_sticker_id"] == 1
    
    # Check Winding template
    winding = next((t for t in templates if t["name"] == "Winding"), None)
    assert winding is not None
    assert winding["short_name"] == "WND"
    assert winding["t_max"] == 100
    assert winding["t_excess"] == 50
    assert winding["default_sticker_id"] == 2


def test_multiple_equipment_types_with_different_templates(client: TestClient):
    """Test that different equipment types have different templates"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Find equipment type 2 (Transformer)
    transformer = next((item for item in items if item["id"] == 2), None)
    assert transformer is not None
    assert transformer["name"] == "Transformer"
    
    # Should have 3 control point templates
    assert len(transformer["control_point_templates"]) == 3
    
    # Verify template names
    template_names = [t["name"] for t in transformer["control_point_templates"]]
    assert "Core" in template_names
    assert "Winding Primary" in template_names
    assert "Winding Secondary" in template_names