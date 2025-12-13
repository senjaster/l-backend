"""Integration tests for Image API"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


def test_create_image(client: TestClient):
    """Test creating a new image"""
    image_id = uuid4()
    equipment_id = uuid4()
    
    image_data = {
        "id": str(image_id),
        "equipment_id": str(equipment_id),
        "original_file_name": "test_image.jpg",
        "image_type": "VISUAL",
        "metadata": {"camera": "Canon EOS", "resolution": "1920x1080"},
        "server_modified_at": "2024-01-01T00:00:00Z"
    }
    
    response = client.put(f"/image/{image_id}", json=image_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(image_id)
    assert data["equipment_id"] == str(equipment_id)
    assert data["original_file_name"] == "test_image.jpg"
    assert data["image_type"] == "VISUAL"
    assert data["metadata"]["camera"] == "Canon EOS"


def test_get_image(client: TestClient):
    """Test retrieving an image"""
    image_id = uuid4()
    equipment_id = uuid4()
    
    # First create
    image_data = {
        "id": str(image_id),
        "equipment_id": str(equipment_id),
        "original_file_name": "test_image.jpg",
        "image_type": "THERMAL",
        "metadata": None,
        "server_modified_at": "2024-01-01T00:00:00Z"
    }
    client.put(f"/image/{image_id}", json=image_data)
    
    # Then get
    response = client.get(f"/image/{image_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(image_id)
    assert data["image_type"] == "THERMAL"


def test_get_nonexistent_image(client: TestClient):
    """Test retrieving a non-existent image"""
    image_id = uuid4()
    response = client.get(f"/image/{image_id}")
    assert response.status_code == 404


def test_update_image(client: TestClient):
    """Test updating an image"""
    image_id = uuid4()
    equipment_id = uuid4()
    
    # Create initial
    image_data = {
        "id": str(image_id),
        "equipment_id": str(equipment_id),
        "original_file_name": "original.jpg",
        "image_type": "VISUAL",
        "metadata": None,
        "server_modified_at": "2024-01-01T00:00:00Z"
    }
    client.put(f"/image/{image_id}", json=image_data)
    
    # Update
    updated_data = {
        "id": str(image_id),
        "equipment_id": str(equipment_id),
        "original_file_name": "updated.jpg",
        "image_type": "THERMAL",
        "metadata": {"updated": True},
        "server_modified_at": "2024-01-02T00:00:00Z"
    }
    response = client.put(f"/image/{image_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["original_file_name"] == "updated.jpg"
    assert data["image_type"] == "THERMAL"
    assert data["metadata"]["updated"] is True


def test_delete_image(client: TestClient):
    """Test actual deletion of image"""
    image_id = uuid4()
    equipment_id = uuid4()
    
    # Create
    image_data = {
        "id": str(image_id),
        "equipment_id": str(equipment_id),
        "original_file_name": "test.jpg",
        "image_type": "VISUAL",
        "metadata": None,
        "server_modified_at": "2024-01-01T00:00:00Z"
    }
    client.put(f"/image/{image_id}", json=image_data)
    
    # Delete
    response = client.delete(f"/image/{image_id}")
    assert response.status_code == 204
    
    # Verify it's actually deleted (should return 404)
    get_response = client.get(f"/image/{image_id}")
    assert get_response.status_code == 404


def test_id_mismatch(client: TestClient):
    """Test ID mismatch in URL and body"""
    image_id_1 = uuid4()
    image_id_2 = uuid4()
    equipment_id = uuid4()
    
    image_data = {
        "id": str(image_id_2),
        "equipment_id": str(equipment_id),
        "original_file_name": "test.jpg",
        "image_type": "VISUAL",
        "metadata": None,
        "server_modified_at": "2024-01-01T00:00:00Z"
    }
    
    response = client.put(f"/image/{image_id_1}", json=image_data)
    assert response.status_code == 400


def test_image_types(client: TestClient):
    """Test both image types"""
    for image_type in ["VISUAL", "THERMAL"]:
        image_id = uuid4()
        equipment_id = uuid4()
        
        image_data = {
            "id": str(image_id),
            "equipment_id": str(equipment_id),
            "original_file_name": f"test_{image_type.lower()}.jpg",
            "image_type": image_type,
            "metadata": None,
            "server_modified_at": "2024-01-01T00:00:00Z"
        }
        
        response = client.put(f"/image/{image_id}", json=image_data)
        assert response.status_code == 200
        assert response.json()["image_type"] == image_type