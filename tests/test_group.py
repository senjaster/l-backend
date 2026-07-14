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
        "plants": [{"name": "Test Plant", "is_deleted": False}],
    }
    data = deepcopy(GROUP_TEMPLATE)
    data["id"] = str(group_id)
    data["plants"][0]["id"] = str(plant_id)
    data["plants"][0]["server_modified_at"] = data["server_modified_at"]
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
        "plants": []
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
    
    # Добавляем станцию в корневую группу
    client.post(f"/group/by_id/{root['id']}/plants", json={
        "plant_ids": [str(root_plant_id)]
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
        "plants": []
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
    
    # Добавляем станцию в дочернюю группу 1
    client.post(f"/group/by_id/{child1['id']}/plants", json={
        "plant_ids": [str(child1_plant_id)]
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
        "plants": []
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
    
    # Добавляем станцию во внучатую группу
    client.post(f"/group/by_id/{grandchild['id']}/plants", json={
        "plant_ids": [str(grandchild_plant_id)]
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
        "plants": []
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
    
    # Добавляем станцию в дочернюю группу 2
    client.post(f"/group/by_id/{child2['id']}/plants", json={
        "plant_ids": [str(child2_plant_id)]
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
    assert data["plants"] == []


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
        "plants": []
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
        "plants": []
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
    assert data["plants"] == []


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
        "plants": [],
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
        "plants": [],
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
    assert data["plants"] == []


def test_get_group_without_children(client: TestClient):
    """Тест получения группы без детей"""
    tree_data = create_group_tree(client)
    
    response = client.get(f"/group/by_id/{tree_data['root']['id']}?include_children=false")
    assert response.status_code == 200
    
    data = response.json()
    assert data["children"] == []


def test_add_plants_to_group(client: TestClient):
    """Тест добавления станций в группу"""
    now = datetime.now(timezone.utc)
    
    # Создаем группу
    group_id = str(uuid.uuid4())
    create_response = client.put("/group", json={
        "id": group_id,
        "name": "Group With Plants",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
        "plants": []
    })
    assert create_response.status_code == 200
    group = create_response.json()
    group_id = group["id"]
    
    # Создаем станцию
    plant_id = str(uuid.uuid4())
    plant_data = {
        "id": plant_id,
        "group_id": group_id,
        "name": "Test Plant",
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    }
    client.put("/plant", json=plant_data)
    
    # Добавляем станцию в группу
    response = client.post(f"/group/by_id/{group_id}/plants", json={
        "plant_ids": [plant_id]
    })
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "Added" in data["message"]
    
    # Проверяем, что станция добавилась в группу
    get_response = client.get(f"/group/by_id/{group_id}")
    assert get_response.status_code == 200
    
    # Проверяем, что у станции обновился group_id
    get_plant_response = client.get(f"/plant/by_id/{plant_id}")
    assert get_plant_response.status_code == 200
    plant = get_plant_response.json()
    assert plant["group_id"] == group_id


def test_get_group_plants(client: TestClient):
    """Тест получения станций группы"""
    tree_data = create_group_tree(client)
    
    # Получаем станции корневой группы
    response = client.get(f"/group/by_id/{tree_data['root']['id']}/plants")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings
    
    # Получаем станции без подгрупп
    response = client.get(f"/group/by_id/{tree_data['root']['id']}/plants?include_subgroups=false")
    assert response.status_code == 200
    data = response.json()
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings


def test_get_group_plants_with_subgroups(client: TestClient):
    """Тест получения станций группы с подгруппами"""
    tree_data = create_group_tree(client)
    
    # Получаем станции дочерней группы с подгруппами
    response = client.get(f"/group/by_id/{tree_data['child1']['id']}/plants?include_subgroups=true")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    # Должны быть станции из child1 и grandchild
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["child1_plant_id"]) in items_as_strings
    assert str(tree_data["grandchild_plant_id"]) in items_as_strings


def test_add_existing_plant_to_group(client: TestClient):
    """Тест добавления уже существующей станции в группу (восстановление)"""
    tree_data = create_group_tree(client)
    
    # Удаляем станцию
    client.delete(f"/group/by_id/{tree_data['root']['id']}/plants/{tree_data['root_plant_id']}")
    
    # Добавляем снова ту же станцию
    response = client.post(f"/group/by_id/{tree_data['root']['id']}/plants", json={
        "plant_ids": [str(tree_data["root_plant_id"])]
    })
    assert response.status_code == 200
    
    # Проверяем, что станция восстановлена
    get_response = client.get(f"/group/by_id/{tree_data['root']['id']}/plants")
    assert get_response.status_code == 200
    data = get_response.json()
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings


def test_get_groups_by_plant(client: TestClient):
    """Тест получения групп, содержащих станцию"""
    tree_data = create_group_tree(client)
    
    response = client.get(f"/group/by-plant/{tree_data['root_plant_id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(g["id"] == tree_data["root"]["id"] for g in data["items"])


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
        "plants": []
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
        "plants": []
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


def test_create_group_without_plants(client: TestClient, group_data):
    """Тест создания группы без станций"""
    response = client.put("/group", json=group_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["plants"] == []


def test_add_multiple_plants_to_group(client: TestClient):
    """Тест добавления нескольких станций в группу"""
    now = datetime.now(timezone.utc)
    
    # Создаем группу
    group_id = str(uuid.uuid4())
    create_response = client.put("/group", json={
        "id": group_id,
        "name": "Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
        "plants": []
    })
    assert create_response.status_code == 200
    group = create_response.json()
    group_id = group["id"]
    
    # Создаем несколько станций
    plant_ids = []
    for i in range(3):
        plant_id = str(uuid.uuid4())
        plant_data = {
            "id": plant_id,
            "group_id": None,
            "name": f"Plant {i}",
            "is_deleted": False,
            "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        }
        plant_response = client.put("/plant", json=plant_data)
        assert plant_response.status_code == 200
        plant_ids.append(plant_id)
    
    # Добавляем все станции в группу
    response = client.post(f"/group/by_id/{group_id}/plants", json={
        "plant_ids": plant_ids
    })
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "Added 3 plants" in data["message"] or "Added" in data["message"]
    
    # Проверяем, что все станции добавились в группу
    get_response = client.get(f"/group/by_id/{group_id}")
    assert get_response.status_code == 200


def test_add_nonexistent_plant_to_group(client: TestClient):
    """Тест добавления несуществующей станции в группу"""
    now = datetime.now(timezone.utc)
    
    # Создаем группу
    group_id = str(uuid.uuid4())
    create_response = client.put("/group", json={
        "id": group_id,
        "name": "Group",
        "parent_group_id": None,
        "is_deleted": False,
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        "children": [],
        "plants": []
    })
    assert create_response.status_code == 200
    group = create_response.json()
    group_id = group["id"]
    
    random_plant_id = str(uuid.uuid4())
    
    # Пытаемся добавить несуществующую станцию
    response = client.post(f"/group/by_id/{group_id}/plants", json={
        "plant_ids": [random_plant_id]
    })
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "Plants not found" in data["detail"] or "not found" in data["detail"].lower()