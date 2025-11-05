"""Integration tests for authentication API"""
import pytest
from fastapi.testclient import TestClient
from app.shared.test_base import client


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication API endpoints"""

    def test_register_success(self, client: TestClient):
        """Test successful user registration via API"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be in response

    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email via API"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient):
        """Test successful login via API"""
        # Arrange - Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Login with form data
        login_data = {
            "username": "test@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_success(self, client: TestClient):
        """Test successful login via JSON endpoint"""
        # Arrange - Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Login with JSON
        login_data = {
            "email": "test@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/auth/login/json", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password"""
        # Arrange - Register user first
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Login with wrong password
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)

        # Assert
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient):
        """Test getting current user info"""
        # Arrange - Register and login
        user_data = {
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "username": "test@example.com",
            "password": "securepass123"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # Act - Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        # Act
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        # Assert
        assert response.status_code == 401