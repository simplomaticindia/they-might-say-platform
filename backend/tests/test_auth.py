"""Test authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAuth:
    """Test authentication functionality."""

    def test_register_user(self, client: TestClient):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_user(self, client: TestClient, test_user):
        """Test registration with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123",
                "full_name": "Different User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "password123",
                "full_name": "Different User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "secret"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient, test_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_get_current_user(self, client: TestClient, auth_headers, test_user):
        """Test getting current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_logout(self, client: TestClient, auth_headers):
        """Test user logout."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_refresh_token(self, client: TestClient, test_user):
        """Test token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "secret"
            }
        )
        assert login_response.status_code == 200
        
        # Use refresh token to get new access token
        refresh_token = login_response.json().get("refresh_token")
        if refresh_token:
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_password_validation(self, client: TestClient):
        """Test password validation requirements."""
        # Test short password
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser2",
                "email": "test2@example.com",
                "password": "123",
                "full_name": "Test User 2"
            }
        )
        assert response.status_code == 422

    def test_email_validation(self, client: TestClient):
        """Test email validation."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser3",
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Test User 3"
            }
        )
        assert response.status_code == 422

    def test_username_validation(self, client: TestClient):
        """Test username validation."""
        # Test empty username
        response = client.post(
            "/api/auth/register",
            json={
                "username": "",
                "email": "test4@example.com",
                "password": "password123",
                "full_name": "Test User 4"
            }
        )
        assert response.status_code == 422

        # Test username with special characters
        response = client.post(
            "/api/auth/register",
            json={
                "username": "test@user",
                "email": "test5@example.com",
                "password": "password123",
                "full_name": "Test User 5"
            }
        )
        assert response.status_code == 422