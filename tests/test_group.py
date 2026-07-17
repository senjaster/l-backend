"""Integration tests for Group API"""

import pytest
import time
import uuid
from datetime import datetime, timezone
from copy import deepcopy
from fastapi.testclient import TestClient


PUT_BODY_TEMPLATE = {
    "id": None,  # filled per test
    "name": "Test Group",
    "parent_group_id": None,
    "is_deleted": False,
    "server_modified_at": "2024-01-01T00:00:00Z",
}


@pytest.fixture
def group_id():
    return uuid.uuid4()


@pytest.fixture
def group_data(group_id):
    """Minimal valid PUT body for a group."""
    data = deepcopy(PUT_BODY_TEMPLATE)
    data["id"] = str(group_id)
    return data


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def test_create_group(client: TestClient, group_data):
    """Create a new root group and verify the response fields."""
    response = client.put("/group", json=group_data)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == group_data["id"]
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] is None
    assert data["is_deleted"] is False
    assert "server_modified_at" in data


def test_create_group_with_parent(client: TestClient):
    """Create a child group referencing an existing parent."""
    parent_id = str(uuid.uuid4())
    parent_response = client.put("/group", json={
        "id": parent_id,
        "name": "Parent Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert parent_response.status_code == 200

    child_id = str(uuid.uuid4())
    response = client.put("/group", json={
        "id": child_id,
        "name": "Child Group",
        "parent_group_id": parent_id,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == child_id
    assert data["parent_group_id"] == parent_id
    assert data["is_deleted"] is False
    assert "server_modified_at" in data


def test_create_group_with_nonexistent_parent(client: TestClient):
    """Creating a group with a non-existent parent_group_id triggers a FK violation → 400."""
    nonexistent_id = str(uuid.uuid4())
    response = client.put("/group", json={
        "id": str(uuid.uuid4()),
        "name": "Orphan Group",
        "parent_group_id": nonexistent_id,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "foreign_key_violation"


def test_get_group(client: TestClient, group_data):
    """GET /group/by_id/{id} returns the created group."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    group_id = create_response.json()["id"]

    response = client.get(f"/group/by_id/{group_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == group_id
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] == group_data["parent_group_id"]


def test_get_nonexistent_group(client: TestClient):
    """GET /group/by_id/{id} returns 404 for an unknown ID."""
    response = client.get(f"/group/by_id/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_group(client: TestClient, group_data):
    """Update an existing group name; server_modified_at must advance."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()
    server_modified_at = created["server_modified_at"]

    updated_data = {
        "id": created["id"],
        "name": "Updated Group Name",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": server_modified_at,
    }
    response = client.put("/group", json=updated_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Group Name"
    assert data["is_deleted"] is False
    assert data["server_modified_at"] != server_modified_at


def test_logical_deletion(client: TestClient, group_data):
    """Setting is_deleted=True persists and is returned by GET."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()

    deleted_data = {
        "id": created["id"],
        "name": created["name"],
        "parent_group_id": None,
        "is_deleted": True,
        "server_modified_at": created["server_modified_at"],
    }
    response = client.put("/group", json=deleted_data)
    assert response.status_code == 200
    assert response.json()["is_deleted"] is True

    # GET still returns the group (logical deletion, not physical)
    get_response = client.get(f"/group/by_id/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["is_deleted"] is True


# ---------------------------------------------------------------------------
# Optimistic locking
# ---------------------------------------------------------------------------

def test_optimistic_locking_conflict(client: TestClient, group_data):
    """PUT with a stale server_modified_at returns 409."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200

    # Use the original (now stale) timestamp from the template
    stale_data = {
        "id": group_data["id"],
        "name": "Conflict Update",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2000-01-01T00:00:00Z",  # definitely stale
    }
    response = client.put("/group", json=stale_data)
    assert response.status_code == 409
    body = response.json()
    # Router raises HTTPException(detail=...), so FastAPI wraps it as {"detail": {...}}
    assert body["detail"]["type"] == "conflict"
    assert "server_modified_at" in body["detail"]


def test_optimistic_locking_success(client: TestClient, group_data):
    """PUT with the correct server_modified_at succeeds."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()

    update_data = {
        "id": created["id"],
        "name": "Correct Update",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": created["server_modified_at"],
    }
    response = client.put("/group", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Correct Update"


def test_force_bypasses_optimistic_locking(client: TestClient, group_data):
    """PUT with force=true ignores stale server_modified_at and succeeds."""
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200

    stale_data = {
        "id": group_data["id"],
        "name": "Force Update",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2000-01-01T00:00:00Z",  # stale
    }
    response = client.put("/group?force=true", json=stale_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Force Update"


# ---------------------------------------------------------------------------
# Cyclic dependency guard
# ---------------------------------------------------------------------------

def test_self_reference_rejected(client: TestClient):
    """A group cannot be its own parent → 400."""
    group_id = str(uuid.uuid4())
    # First create the group
    create_response = client.put("/group", json={
        "id": group_id,
        "name": "Self Ref Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert create_response.status_code == 200
    created = create_response.json()

    # Now try to set parent_group_id = own id
    response = client.put("/group", json={
        "id": group_id,
        "name": "Self Ref Group",
        "parent_group_id": group_id,
        "is_deleted": False,
        "server_modified_at": created["server_modified_at"],
    })
    assert response.status_code == 400


def test_cyclic_dependency_rejected(client: TestClient):
    """Moving a group to one of its own descendants creates a cycle → 400."""
    # Create: A → B → C, then try to set A's parent to C
    a_id = str(uuid.uuid4())
    b_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())

    a_resp = client.put("/group", json={
        "id": a_id, "name": "A", "parent_group_id": None,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert a_resp.status_code == 200
    a = a_resp.json()

    b_resp = client.put("/group", json={
        "id": b_id, "name": "B", "parent_group_id": a_id,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert b_resp.status_code == 200

    c_resp = client.put("/group", json={
        "id": c_id, "name": "C", "parent_group_id": b_id,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert c_resp.status_code == 200

    # Try to move A under C (would create A→B→C→A cycle)
    response = client.put("/group", json={
        "id": a_id, "name": "A", "parent_group_id": c_id,
        "is_deleted": False, "server_modified_at": a["server_modified_at"],
    })
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

def test_get_all_groups(client: TestClient):
    """GET /group/all returns {"items": [...]} containing created groups."""
    g1_id = str(uuid.uuid4())
    g2_id = str(uuid.uuid4())

    r1 = client.put("/group", json={
        "id": g1_id, "name": "List Group 1", "parent_group_id": None,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert r1.status_code == 200

    r2 = client.put("/group", json={
        "id": g2_id, "name": "List Group 2", "parent_group_id": None,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert r2.status_code == 200

    response = client.get("/group/all")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    ids = [g["id"] for g in body["items"]]
    assert g1_id in ids
    assert g2_id in ids


def test_get_all_groups_with_modified_since(client: TestClient):
    """GET /group/all?modified_since=<ts> filters out groups modified before that timestamp."""
    # Create first group and record its server_modified_at
    g1_id = str(uuid.uuid4())
    r1 = client.put("/group", json={
        "id": g1_id, "name": "Before Group", "parent_group_id": None,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert r1.status_code == 200
    timestamp_after_g1 = r1.json()["server_modified_at"]

    time.sleep(0.05)

    # Create second group after the cutoff
    g2_id = str(uuid.uuid4())
    r2 = client.put("/group", json={
        "id": g2_id, "name": "After Group", "parent_group_id": None,
        "is_deleted": False, "server_modified_at": "2024-01-01T00:00:00Z",
    })
    assert r2.status_code == 200

    # Filter: only groups modified strictly after g1's timestamp
    response = client.get(f"/group/all?modified_since={timestamp_after_g1}")
    assert response.status_code == 200
    filtered_ids = [g["id"] for g in response.json()["items"]]
    assert g1_id not in filtered_ids
    assert g2_id in filtered_ids
