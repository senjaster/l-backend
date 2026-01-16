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

    # Should have 6 equipment types from init_db.sql
    assert len(items) == 6

    # Verify structure of first item
    assert all(
        key in items[0]
        for key in ["id", "name", "server_modified_at", "control_point_templates"]
    )


def test_equipment_type_with_templates(client: TestClient):
    """Test that equipment types include their control point templates"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find equipment type 1 (Электродвигатель 0,4 кВ - подшипник качения)
    motor = next((item for item in items if item["id"] == 1), None)
    assert motor is not None
    assert "Электродвигатель" in motor["name"]

    # Should have 4 control point templates
    assert len(motor["control_point_templates"]) == 4

    # Verify template structure
    template = motor["control_point_templates"][0]
    assert all(
        key in template
        for key in [
            "id",
            "equipment_type_id",
            "name",
            "short_name",
            "t_max",
            "t_excess",
            "default_sticker_id",
        ]
    )


def test_equipment_type_template_values(client: TestClient):
    """Test control point template values are correct"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find equipment type 1 (Электродвигатель 0,4 кВ - подшипник качения)
    motor = next((item for item in items if item["id"] == 1), None)
    assert motor is not None

    # Verify templates
    templates = motor["control_point_templates"]
    assert len(templates) == 4

    # Check Передний подшипник template
    front_bearing = next(
        (t for t in templates if t["name"] == "Передний подшипник"), None
    )
    assert front_bearing is not None
    assert front_bearing["short_name"] == "ПП"
    assert front_bearing["t_max"] == 100
    assert front_bearing["t_excess"] == 60
    assert front_bearing["default_sticker_id"] == 3

    # Check Корпус template
    korpus = next((t for t in templates if t["name"] == "Корпус"), None)
    assert korpus is not None
    assert korpus["short_name"] == "Корпус"
    assert korpus["t_max"] == 100
    assert korpus["t_excess"] == 60
    assert korpus["default_sticker_id"] == 2


def test_multiple_equipment_types_with_different_templates(client: TestClient):
    """Test that different equipment types have different templates"""
    response = client.get("/equipment-type/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find equipment type 2 (Электродвигатель 0,4 кВ - подшипник скольжения)
    motor2 = next((item for item in items if item["id"] == 2), None)
    assert motor2 is not None
    assert "подшипник скольжения" in motor2["name"]

    # Should have 4 control point templates
    assert len(motor2["control_point_templates"]) == 4

    # Verify template names
    template_names = [t["name"] for t in motor2["control_point_templates"]]
    assert "Передний подшипник" in template_names
    assert "Задний подшипник" in template_names
    assert "Корпус" in template_names
    assert "Блок распределения начала обмоток" in template_names


# Tests for modified_since filter


def test_get_all_equipment_types_with_modified_since_filter(client: TestClient):
    """Test filtering equipment types by modified_since parameter"""
    # Note: Equipment types are seeded data, so we can't easily create new ones with different timestamps
    # This test verifies the parameter works without errors

    # Get all equipment types without filter
    response = client.get("/equipment-type/all")
    assert response.status_code == 200
    all_types = response.json()["items"]
    assert len(all_types) == 6

    # Get equipment types with a very old timestamp - should return all
    response = client.get("/equipment-type/all?modified_since=1900-01-01T00:00:00Z")
    assert response.status_code == 200
    filtered_types = response.json()["items"]
    assert len(filtered_types) == 6

    # Get equipment types with a future timestamp - should return none
    response = client.get("/equipment-type/all?modified_since=2099-12-31T23:59:59Z")
    assert response.status_code == 200
    filtered_types = response.json()["items"]
    assert len(filtered_types) == 0
