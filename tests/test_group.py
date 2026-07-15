"""Integration tests for Group API"""

import pytest
import time
import uuid
from datetime import datetime, timezone
from copy import deepcopy
from fastapi.testclient import TestClient


now = datetime.now(timezone.utc)


@pytest.fixture
def group_id():
    return uuid.uuid4()


@pytest.fixture
def plant_id():
    return uuid.uuid4()


@pytest.fixture
def group_data(group_id, plant_id):
    """Создание тестовой группы"""
    GROUP_TEMPLATE = {
        "name": "Test Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
        "children": [],
    }
    data = deepcopy(GROUP_TEMPLATE)
    data["id"] = str(group_id)
    return data


@pytest.fixture
def plant_data(plant_id):
    """Создание тестовой станции"""
    return {
        "id": str(plant_id),
        "name": "Test Plant",
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    }


def create_group_tree(client):
    """
    Создание тестовой структуры групп:
    - Root Group (уровень 0)
      - Child Group 1 (уровень 1)
        - Grandchild Group 1 (уровень 2)
      - Child Group 2 (уровень 1)
    """
    now = datetime.now(timezone.utc)
    
    # Создаем корневую группу
    root_id = str(uuid.uuid4())
    root_response = client.put("/group", json={
        "id": root_id,
        "name": "Root Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert root_response.status_code == 200
    root = root_response.json()
    
    # Создаем станцию для корневой группы
    root_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(root_plant_id),
        "group_id": root_id,
        "name": "Root Plant",
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    })
    
    # Создаем дочернюю группу 1
    child1_id = str(uuid.uuid4())
    child1_response = client.put("/group", json={
        "id": child1_id,
        "name": "Child Group 1",
        "parent_group_id": root['id'],
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert child1_response.status_code == 200
    child1 = child1_response.json()
    
    # Создаем станцию для дочерней группы 1
    child1_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(child1_plant_id),
        "group_id": child1_id,
        "name": "Child 1 Plant",
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    })
    
    # Создаем внучатую группу (уровень 2)
    grandchild_id = str(uuid.uuid4())
    grandchild_response = client.put("/group", json={
        "id": grandchild_id,
        "name": "Grandchild Group 1",
        "parent_group_id": child1['id'],
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert grandchild_response.status_code == 200
    grandchild = grandchild_response.json()
    
    # Создаем станцию для внучатой группы
    grandchild_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(grandchild_plant_id),
        "group_id": grandchild_id,
        "name": "Grandchild Plant",
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    })
    
    # Создаем дочернюю группу 2
    child2_id = str(uuid.uuid4())
    child2_response = client.put("/group", json={
        "id": child2_id,
        "name": "Child Group 2",
        "parent_group_id": root['id'],
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert child2_response.status_code == 200
    child2 = child2_response.json()
    
    # Создаем станцию для дочерней группы 2
    child2_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(child2_plant_id),
        "group_id": child2_id,
        "name": "Child 2 Plant",
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    })
    
    return {
        "root": root,
        "child1": child1,
        "child2": child2,
        "grandchild": grandchild,
        "root_plant_id": root_plant_id,
        "child1_plant_id": child1_plant_id,
        "child2_plant_id": child2_plant_id,
        "grandchild_plant_id": grandchild_plant_id
    }


def test_create_group(client: TestClient, group_data):
    """Тест создания группы"""
    response = client.put("/group", json=group_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] == group_data["parent_group_id"]
    assert data["is_deleted"] is False
    assert "server_modified_at" in data
    assert data["children"] == []


def test_create_group_with_parent(client: TestClient, group_id):
    """Тест создания группы с родителем"""
    # Генерируем ID для дочерней группы
    child_id = str(uuid.uuid4())
    
    # Сначала создаем родительскую группу
    parent_group_data = {
        "id": str(group_id),
        "name": "Parent Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
        "children": [],
    }
    parent_response = client.put("/group", json=parent_group_data)
    assert parent_response.status_code == 200
    parent = parent_response.json()
    
    # Создаем дочернюю группу
    child_group_data = {
        "id": child_id,
        "name": "Child Group",
        "parent_group_id": parent['id'],
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
        "children": [],
    }
    response = client.put("/group", json=child_group_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["name"] == child_group_data["name"]
    assert data["parent_group_id"] == parent['id']
    assert data["is_deleted"] is False
    assert "server_modified_at" in data
    assert data["children"] == []


def test_create_group_with_nonexistent_parent(client: TestClient, group_id):
    """Тест создания группы с несуществующим родителем"""
    nonexistent_id = str(uuid.uuid4())
    group_data = {
        "id": str(group_id),
        "name": "Child Group",
        "parent_group_id": nonexistent_id,
        "is_deleted": False,
        "server_modified_at": "2024-01-01T00:00:00Z",
        "children": [],
    }
    response = client.put("/group", json=group_data)
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_get_group(client: TestClient, group_data):
    """Тест получения группы по ID"""
    # Создаем группу
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()
    group_id = created["id"]
    
    # Получаем группу
    response = client.get(f"/group/by_id/{group_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == group_id
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] == group_data["parent_group_id"]


def test_get_nonexistent_group(client: TestClient):
    """Тест получения несуществующей группы"""
    group_id = uuid.uuid4()
    response = client.get(f"/group/by_id/{group_id}")
    assert response.status_code == 404


def test_update_group(client: TestClient, group_data):
    """Тест обновления группы"""
    # Создаем группу
    create_response = client.put("/group", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()
    group_id = created["id"]
    
    server_modified_at = created["server_modified_at"]
    
    # Обновляем группу
    updated_data = {
        "id": group_id,
        "name": "Updated Group Name",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": server_modified_at,
        "children": [],
    }
    response = client.put(f"/group", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["name"] == "Updated Group Name"
    assert data["parent_group_id"] is None
    assert data["is_deleted"] is False
    assert "server_modified_at" in data
    assert data["children"] == []


def test_get_all_groups_with_modified_since(client: TestClient):
    """Тест получения групп с фильтром по дате изменения"""
    now = datetime.now(timezone.utc)
    
    # Создаем первую группу
    group1_id = str(uuid.uuid4())
    response1 = client.put("/group", json={
        "id": group1_id,
        "name": "Group 1",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert response1.status_code == 200
    group1 = response1.json()
    group1_id = group1["id"]
    timestamp1 = group1["server_modified_at"]
    
    time.sleep(0.1)
    
    # Создаем вторую группу
    now2 = datetime.now(timezone.utc)
    group2_id = str(uuid.uuid4())
    response2 = client.put("/group", json={
        "id": group2_id,
        "name": "Group 2",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now2.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
    })
    assert response2.status_code == 200
    group2 = response2.json()
    group2_id = group2["id"]
    timestamp2 = group2["server_modified_at"]
    
    # Получаем все группы
    response = client.get("/group/all")
    assert response.status_code == 200
    all_groups = response.json()["items"]
    group_ids = [g["id"] for g in all_groups]
    assert group1_id in group_ids
    assert group2_id in group_ids
    
    # Получаем группы после timestamp1
    response = client.get(f"/group/all?modified_since={timestamp1}")
    assert response.status_code == 200
    filtered_groups = response.json()["items"]
    filtered_ids = [g["id"] for g in filtered_groups]
    assert group1_id not in filtered_ids
    assert group2_id in filtered_ids
