"""Integration tests for Group API"""

import pytest
import time
import uuid
from datetime import datetime, timezone
from copy import deepcopy
from fastapi.testclient import TestClient

now = datetime.now(timezone.utc)

GROUP_TEMPLATE = {
    "name": "Test Group",
    "parent_group_id": None
}


@pytest.fixture
def plant_id():
    return uuid.uuid4()


@pytest.fixture
def group_data():
    """Создание тестовой группы"""
    return deepcopy(GROUP_TEMPLATE)


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
    # Создаем корневую группу
    root_response = client.post("/groups", json={
        "name": "Root Group",
        "parent_group_id": None
    })
    assert root_response.status_code == 200
    root = root_response.json()
    
    # Создаем станцию для корневой группы
    root_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(root_plant_id),
        "name": "Root Plant",
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    })
    
    # Добавляем станцию в корневую группу
    client.post(f"/groups/{root['id']}/plants", json={
        "plant_ids": [str(root_plant_id)]
    })
    
    # Создаем дочернюю группу 1
    child1_response = client.post("/groups", json={
        "name": "Child Group 1",
        "parent_group_id": root['id']
    })
    assert child1_response.status_code == 200
    child1 = child1_response.json()
    
    # Создаем станцию для дочерней группы 1
    child1_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(child1_plant_id),
        "name": "Child 1 Plant",
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    })
    
    # Добавляем станцию в дочернюю группу 1
    client.post(f"/groups/{child1['id']}/plants", json={
        "plant_ids": [str(child1_plant_id)]
    })
    
    # Создаем внучатую группу (уровень 2)
    grandchild_response = client.post("/groups", json={
        "name": "Grandchild Group 1",
        "parent_group_id": child1['id']
    })
    assert grandchild_response.status_code == 200
    grandchild = grandchild_response.json()
    
    # Создаем станцию для внучатой группы
    grandchild_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(grandchild_plant_id),
        "name": "Grandchild Plant",
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    })
    
    # Добавляем станцию во внучатую группу
    client.post(f"/groups/{grandchild['id']}/plants", json={
        "plant_ids": [str(grandchild_plant_id)]
    })
    
    # Создаем дочернюю группу 2
    child2_response = client.post("/groups", json={
        "name": "Child Group 2",
        "parent_group_id": root['id']
    })
    assert child2_response.status_code == 200
    child2 = child2_response.json()
    
    # Создаем станцию для дочерней группы 2
    child2_plant_id = uuid.uuid4()
    client.put("/plant", json={
        "id": str(child2_plant_id),
        "name": "Child 2 Plant",
        "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    })
    
    # Добавляем станцию в дочернюю группу 2
    client.post(f"/groups/{child2['id']}/plants", json={
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
    response = client.post("/groups", json=group_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] == group_data["parent_group_id"]
    assert data["is_deleted"] is False
    assert "server_modified_at" in data
    assert data["children"] == []
    assert data["plants"] == []


def test_create_group_with_parent(client: TestClient):
    """Тест создания группы с родителем"""
    # Сначала создаем родительскую группу
    parent_response = client.post("/groups", json={
        "name": "Parent Group",
        "parent_group_id": None
    })
    assert parent_response.status_code == 200
    parent = parent_response.json()
    
    # Создаем дочернюю группу
    response = client.post("/groups", json={
        "name": "Child Group",
        "parent_group_id": parent['id']
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["parent_group_id"] == parent['id']


def test_create_group_with_nonexistent_parent(client: TestClient):
    """Тест создания группы с несуществующим родителем"""
    response = client.post("/groups", json={
        "name": "Child Group",
        "parent_group_id": str(uuid.uuid4())
    })
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_group(client: TestClient, group_data):
    """Тест получения группы по ID"""
    # Создаем группу
    create_response = client.post("/groups", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()
    group_id = created["id"]
    
    # Получаем группу
    response = client.get(f"/groups/{group_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == group_id
    assert data["name"] == group_data["name"]
    assert data["parent_group_id"] == group_data["parent_group_id"]


def test_get_nonexistent_group(client: TestClient):
    """Тест получения несуществующей группы"""
    group_id = uuid.uuid4()
    response = client.get(f"/groups/{group_id}")
    assert response.status_code == 404


def test_update_group(client: TestClient, group_data):
    """Тест обновления группы"""
    # Создаем группу
    create_response = client.post("/groups", json=group_data)
    assert create_response.status_code == 200
    created = create_response.json()
    group_id = created["id"]
    
    # Обновляем группу
    updated_data = {
        "name": "Updated Group Name",
        "parent_group_id": None
    }
    response = client.put(f"/groups/{group_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Group Name"
    assert data["parent_group_id"] is None


def test_get_group_without_children(client: TestClient):
    """Тест получения группы без детей"""
    tree_data = create_group_tree(client)
    
    response = client.get(f"/groups/{tree_data['root']['id']}?include_children=false")
    assert response.status_code == 200
    
    data = response.json()
    assert data["children"] == []


def test_add_plants_to_group(client: TestClient, plant_data):
    """Тест добавления станций в группу"""
    # Создаем группу
    create_response = client.post("/groups", json={
        "name": "Group With Plants",
        "parent_group_id": None
    })
    assert create_response.status_code == 200
    group = create_response.json()
    group_id = group["id"]
    
    # Создаем станцию
    client.put("/plant", json=plant_data)
    
    # Добавляем станцию в группу
    response = client.post(f"/groups/{group_id}/plants", json={
        "plant_ids": [str(plant_data["id"])]
    })
    assert response.status_code == 200
    assert "Added" in response.json()["message"]


def test_get_group_plants(client: TestClient):
    """Тест получения станций группы"""
    tree_data = create_group_tree(client)
    
    # Получаем станции корневой группы
    response = client.get(f"/groups/{tree_data['root']['id']}/plants")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings
    
    # Получаем станции без подгрупп
    response = client.get(f"/groups/{tree_data['root']['id']}/plants?include_subgroups=false")
    assert response.status_code == 200
    data = response.json()
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings


def test_get_group_plants_with_subgroups(client: TestClient):
    """Тест получения станций группы с подгруппами"""
    tree_data = create_group_tree(client)
    
    # Получаем станции дочерней группы с подгруппами
    response = client.get(f"/groups/{tree_data['child1']['id']}/plants?include_subgroups=true")
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
    client.delete(f"/groups/{tree_data['root']['id']}/plants/{tree_data['root_plant_id']}")
    
    # Добавляем снова ту же станцию
    response = client.post(f"/groups/{tree_data['root']['id']}/plants", json={
        "plant_ids": [str(tree_data["root_plant_id"])]
    })
    assert response.status_code == 200
    
    # Проверяем, что станция восстановлена
    get_response = client.get(f"/groups/{tree_data['root']['id']}/plants")
    assert get_response.status_code == 200
    data = get_response.json()
    items_as_strings = [str(item) for item in data["items"]]
    assert str(tree_data["root_plant_id"]) in items_as_strings


def test_get_groups_by_plant(client: TestClient):
    """Тест получения групп, содержащих станцию"""
    tree_data = create_group_tree(client)
    
    response = client.get(f"/groups/by-plant/{tree_data['root_plant_id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(g["id"] == tree_data["root"]["id"] for g in data["items"])


def test_get_all_groups_with_modified_since(client: TestClient):
    """Тест получения групп с фильтром по дате изменения"""
    # Создаем первую группу
    response1 = client.post("/groups", json={
        "name": "Group 1",
        "parent_group_id": None
    })
    group1_id = response1.json()["id"]
    assert response1.status_code == 200
    timestamp1 = response1.json()["server_modified_at"]
    
    time.sleep(0.1)
    
    # Создаем вторую группу
    response2 = client.post("/groups", json={
        "name": "Group 2",
        "parent_group_id": None
    })
    group2_id = response2.json()["id"]
    assert response2.status_code == 200
    timestamp2 = response2.json()["server_modified_at"]
    
    # Получаем все группы
    response = client.get("/groups/all")
    assert response.status_code == 200
    all_groups = response.json()["items"]
    group_ids = [g["id"] for g in all_groups]
    assert str(group1_id) in group_ids
    assert str(group2_id) in group_ids
    
    # Получаем группы после timestamp1
    response = client.get(f"/groups/all?modified_since={timestamp1}")
    assert response.status_code == 200
    filtered_groups = response.json()["items"]
    filtered_ids = [g["id"] for g in filtered_groups]
    assert str(group1_id) not in filtered_ids
    assert str(group2_id) in filtered_ids


def test_create_group_without_plants(client: TestClient, group_data):
    """Тест создания группы без станций"""
    response = client.post("/groups", json=group_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["plants"] == []


def test_add_multiple_plants_to_group(client: TestClient):
    """Тест добавления нескольких станций в группу"""
    # Создаем группу
    create_response = client.post("/groups", json={
        "name": "Group",
        "parent_group_id": None
    })
    assert create_response.status_code == 200
    group_id = create_response.json()["id"]
    
    # Создаем несколько станций
    plant_ids = []
    for i in range(3):
        plant_id = uuid.uuid4()
        client.put("/plant", json={
            "id": str(plant_id),
            "name": f"Plant {i}",
            "server_modified_at": now.isoformat(timespec='seconds').replace('+00:00', 'Z')
        })
        plant_ids.append(str(plant_id))
    
    # Добавляем все станции в группу
    response = client.post(f"/groups/{group_id}/plants", json={
        "plant_ids": plant_ids
    })
    assert response.status_code == 200
    assert "Added 3 plants" in response.json()["message"]


def test_add_nonexistent_plant_to_group(client: TestClient):
    """Тест добавления несуществующей станции в группу"""
    # Создаем группу
    create_response = client.post("/groups", json={
        "name": "Group",
        "parent_group_id": None
    })
    assert create_response.status_code == 200
    group_id = create_response.json()["id"]
    
    random_plant_id = uuid.uuid4()
    
    # Пытаемся добавить несуществующую станцию
    response = client.post(f"/groups/{group_id}/plants", json={
        "plant_ids": [str(random_plant_id)]
    })
    assert response.status_code == 404
    assert "Plants not found" in response.json()["detail"]