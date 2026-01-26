"""Integration tests for FacilityTemplate API"""

import pytest
from fastapi.testclient import TestClient


def test_get_all_facility_templates(client: TestClient):
    """Test retrieving all facility templates"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    items = data["items"]

    # Should have 4 facility templates from init_db.sql
    assert len(items) == 4

    # Verify structure of first item
    assert all(
        key in items[0]
        for key in ["id", "name", "is_multiple_allowed", "server_modified_at", "equipment_templates"]
    )


def test_facility_template_with_equipment_templates(client: TestClient):
    """Test that facility templates include their equipment templates"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find facility template 1 (Хозяйство резервного топлива)
    fuel_facility = next((item for item in items if item["id"] == 1), None)
    assert fuel_facility is not None
    assert fuel_facility["name"] == "Хозяйство резервного топлива"
    assert fuel_facility["is_multiple_allowed"] is False

    # Should have 5 equipment templates
    assert len(fuel_facility["equipment_templates"]) == 5

    # Verify equipment template structure
    template = fuel_facility["equipment_templates"][0]
    assert all(
        key in template
        for key in [
            "id",
            "name",
            "is_container",
            "equipment_type_id",
            "parent_id",
        ]
    )


def test_facility_template_equipment_values(client: TestClient):
    """Test equipment template values are correct"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find facility template 1 (Хозяйство резервного топлива)
    fuel_facility = next((item for item in items if item["id"] == 1), None)
    assert fuel_facility is not None

    # Verify equipment templates
    templates = fuel_facility["equipment_templates"]
    assert len(templates) == 5

    # Check Мазутное хозяйство template
    mazut = next(
        (t for t in templates if t["name"] == "Мазутное хозяйство"), None
    )
    assert mazut is not None
    assert mazut["is_container"] is True
    assert mazut["equipment_type_id"] is None
    assert mazut["parent_id"] is None

    # Check МНС template (child of Мазутное хозяйство)
    mns = next(
        (t for t in templates if t["name"] == "МНС - может повторяться"), None
    )
    assert mns is not None
    assert mns["is_container"] is True
    assert mns["equipment_type_id"] is None
    assert mns["parent_id"] == mazut["id"]


def test_facility_template_with_equipment_types(client: TestClient):
    """Test facility template with equipment that has equipment types"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find facility template 2 (Общестанционное оборудование)
    general_facility = next((item for item in items if item["id"] == 2), None)
    assert general_facility is not None
    assert general_facility["name"] == "Общестанционное оборудование"

    # Should have 13 equipment templates
    assert len(general_facility["equipment_templates"]) == 13

    # Find equipment with equipment_type_id
    щит = next(
        (t for t in general_facility["equipment_templates"] if t["name"] == "Щит 0,4 кВ"), None
    )
    assert щит is not None
    assert щит["equipment_type_id"] == 6  # Щит 0,4 кВ equipment type

    # Find motors
    motors_04 = next(
        (t for t in general_facility["equipment_templates"] 
         if t["name"] == "Двигатели 0,4 кВ" and t["parent_id"] == щит["parent_id"]), None
    )
    assert motors_04 is not None
    assert motors_04["equipment_type_id"] == 2  # Электродвигатель 0,4 кВ


def test_facility_template_multiple_allowed(client: TestClient):
    """Test facility templates with is_multiple_allowed flag"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find facility template 3 (ПГУ - может повторяться)
    pgu = next((item for item in items if item["id"] == 3), None)
    assert pgu is not None
    assert "может повторятся" in pgu["name"]
    assert pgu["is_multiple_allowed"] is True

    # Find facility template 4 (ТГ - может повторяться)
    tg = next((item for item in items if item["id"] == 4), None)
    assert tg is not None
    assert "может повторятся" in tg["name"]
    assert tg["is_multiple_allowed"] is True

    # Verify non-repeatable templates
    fuel_facility = next((item for item in items if item["id"] == 1), None)
    assert fuel_facility["is_multiple_allowed"] is False


def test_facility_template_hierarchical_structure(client: TestClient):
    """Test facility template with hierarchical equipment structure"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Find facility template 4 (ТГ)
    tg = next((item for item in items if item["id"] == 4), None)
    assert tg is not None

    templates = tg["equipment_templates"]
    
    # Find root equipment (Турбинное отделение)
    turb_otd = next(
        (t for t in templates if t["name"] == "Турбинное отделение"), None
    )
    assert turb_otd is not None
    assert turb_otd["parent_id"] is None

    # Find child equipment (Система возбуждения)
    sys_vozb = next(
        (t for t in templates if t["name"] == "Система возбуждения"), None
    )
    assert sys_vozb is not None
    assert sys_vozb["parent_id"] == turb_otd["id"]
    assert sys_vozb["equipment_type_id"] == 1  # Система возбуждения equipment type

    # Find grandchild equipment (Панели)
    panels = next(
        (t for t in templates if t["name"] == "Панели"), None
    )
    assert panels is not None
    assert panels["parent_id"] == sys_vozb["id"]


def test_multiple_facility_templates_with_different_structures(client: TestClient):
    """Test that different facility templates have different structures"""
    response = client.get("/facility-template/all")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    # Verify each template has different number of equipment
    equipment_counts = {item["id"]: len(item["equipment_templates"]) for item in items}
    
    assert equipment_counts[1] == 5  # Хозяйство резервного топлива
    assert equipment_counts[2] == 13  # Общестанционное оборудование
    assert equipment_counts[3] == 2  # ПГУ
    assert equipment_counts[4] == 8  # ТГ


# Tests for modified_since filter


def test_get_all_facility_templates_with_modified_since_filter(client: TestClient):
    """Test filtering facility templates by modified_since parameter"""
    # Get all facility templates without filter
    response = client.get("/facility-template/all")
    assert response.status_code == 200
    all_templates = response.json()["items"]
    assert len(all_templates) == 4

    # Get facility templates with a very old timestamp - should return all
    response = client.get("/facility-template/all?modified_since=1900-01-01T00:00:00Z")
    assert response.status_code == 200
    filtered_templates = response.json()["items"]
    assert len(filtered_templates) == 4

    # Get facility templates with a future timestamp - should return none
    response = client.get("/facility-template/all?modified_since=2099-12-31T23:59:59Z")
    assert response.status_code == 200
    filtered_templates = response.json()["items"]
    assert len(filtered_templates) == 0
