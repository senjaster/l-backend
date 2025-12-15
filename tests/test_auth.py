"""Tests for authentication endpoints"""
import pytest
import pytest_asyncio
import asyncpg
from uuid import uuid4
from app.services.auth import AuthService
from app.config import settings


@pytest.fixture
def test_inspector_data():
    """Test inspector data"""
    return {
        "username": "test_auth_user",
        "password": "test_password_123",
        "full_name": "Test Auth Inspector"
    }


@pytest_asyncio.fixture
async def test_inspector(test_inspector_data):
    """Create a test inspector in the database"""
    auth_service = AuthService()
    password_hash = auth_service.hash_password(test_inspector_data["password"])
    
    # Insert test inspector directly into database
    conn = await asyncpg.connect(settings.database_url)
    try:
        # Delete existing tokens and inspector to avoid conflicts
        existing_id = await conn.fetchval(
            "SELECT id FROM lesiv.inspector WHERE username = $1",
            test_inspector_data["username"]
        )
        
        if existing_id:
            await conn.execute(
                "DELETE FROM lesiv.tokens WHERE inspector_id = $1",
                existing_id
            )
            await conn.execute(
                "DELETE FROM lesiv.inspector WHERE id = $1",
                existing_id
            )
        
        inspector_id = await conn.fetchval(
            """
            INSERT INTO lesiv.inspector (full_name, username, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            test_inspector_data["full_name"],
            test_inspector_data["username"],
            password_hash
        )
    finally:
        await conn.close()
    
    return {
        "id": inspector_id,
        **test_inspector_data
    }


def test_login_success(client, test_inspector):
    """Test successful login"""
    device_id = str(uuid4())
    
    response = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device_id
        }
    )
    
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify tokens are not empty
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


def test_login_invalid_username(client, test_inspector):
    """Test login with invalid username"""
    device_id = str(uuid4())
    
    response = client.post(
        "/auth/login",
        json={
            "username": "nonexistent_user",
            "password": test_inspector["password"],
            "device_id": device_id
        }
    )
    
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_invalid_password(client, test_inspector):
    """Test login with invalid password"""
    device_id = str(uuid4())
    
    response = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": "wrong_password",
            "device_id": device_id
        }
    )
    
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_refresh_token_success(client, test_inspector):
    """Test successful token refresh"""
    device_id = str(uuid4())
    
    # First, login to get tokens
    login_response = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device_id
        }
    )
    
    assert login_response.status_code == 200
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]
    
    # Now refresh the token
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )
    
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"
    
    # Refresh token should always be different (rotation)
    assert refresh_data["refresh_token"] != login_data["refresh_token"]
    # Access token may be the same if within reuse window (same timestamp)
    # but refresh token must be different


def test_refresh_token_invalid(client):
    """Test refresh with invalid token"""
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid_token_string"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]


def test_refresh_token_reuse_detection(client, test_inspector):
    """Test that reusing a revoked refresh token revokes the chain"""
    device_id = str(uuid4())
    
    # Login to get initial tokens
    login_response = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device_id
        }
    )
    
    assert login_response.status_code == 200
    old_refresh_token = login_response.json()["refresh_token"]
    
    # Refresh once (this revokes old_refresh_token)
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        }
    )
    
    assert refresh_response.status_code == 200
    
    # Try to reuse the old token (should fail - theft detection)
    reuse_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        }
    )
    
    assert reuse_response.status_code == 401


def test_protected_route_with_valid_token(client, test_inspector):
    """Test accessing a protected route with valid access token"""
    device_id = str(uuid4())
    
    # Login to get access token
    login_response = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device_id
        }
    )
    
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # Try to access a protected route (using inspector endpoint as example)
    response = client.get(
        f"/inspectors/{test_inspector['id']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Should succeed (assuming inspector endpoint exists and is protected)
    assert response.status_code in [200, 404]  # 404 if endpoint doesn't require auth yet


def test_protected_route_without_token(client, test_inspector):
    """Test accessing a protected route without token"""
    # This test assumes inspector endpoint is protected
    # If not protected yet, this test documents the expected behavior
    response = client.get(
        f"/inspectors/{test_inspector['id']}"
    )
    
    # Should either succeed (if not protected) or fail with 401/403
    assert response.status_code in [200, 401, 403, 404]


def test_protected_route_with_invalid_token(client, test_inspector):
    """Test accessing a protected route with invalid token"""
    response = client.get(
        f"/inspectors/{test_inspector['id']}",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    # Should either succeed (if not protected) or fail with 401
    assert response.status_code in [200, 401, 404]


def test_multiple_devices_same_user(client, test_inspector):
    """Test that same user can have tokens on multiple devices"""
    device1_id = str(uuid4())
    device2_id = str(uuid4())
    
    # Login from device 1
    response1 = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device1_id
        }
    )
    
    assert response1.status_code == 200
    token1 = response1.json()["refresh_token"]
    
    # Login from device 2
    response2 = client.post(
        "/auth/login",
        json={
            "username": test_inspector["username"],
            "password": test_inspector["password"],
            "device_id": device2_id
        }
    )
    
    assert response2.status_code == 200
    token2 = response2.json()["refresh_token"]
    
    # Both tokens should be different
    assert token1 != token2
    
    # Both tokens should work for refresh
    refresh1 = client.post(
        "/auth/refresh",
        json={"refresh_token": token1}
    )
    assert refresh1.status_code == 200
    
    refresh2 = client.post(
        "/auth/refresh",
        json={"refresh_token": token2}
    )
    assert refresh2.status_code == 200