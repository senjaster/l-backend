"""Integration tests for StickerType API"""
import pytest
from fastapi.testclient import TestClient


def test_get_all_sticker_types(client: TestClient):
    """Test retrieving all sticker types"""
    response = client.get("/sticker-type/all")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    items = data["items"]
    
    # Should have 3 sticker types (including deleted one)
    assert len(items) == 3
    
    # Verify structure of first item
    assert all(key in items[0] for key in ["id", "name", "is_deleted", "server_modified_at", "temp_ranges"])
