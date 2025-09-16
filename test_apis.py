#!/usr/bin/env python3
"""Pytest test suite for both Axum and ReflectAPI servers."""

import asyncio
from http import HTTPStatus

import httpx
import pytest

from axum_server_client import Client as AxumClient
from axum_server_client.api.users import health_get, user_create, user_get, users_list
from axum_server_client.models import ApiError, CreateUserRequest, Role
from reflect_api_demo_client import AsyncClient as ReflectClient
from reflect_api_demo_client.generated import (
    SharedModelsCreateUserRequest,
    SharedModelsRole,
)


@pytest.fixture
def axum_client():
    """Axum REST API client."""
    return AxumClient(base_url="http://127.0.0.1:8000")


@pytest.fixture  
def reflect_client():
    """ReflectAPI RPC client."""
    return ReflectClient(base_url="http://127.0.0.1:9000")


class TestAxumAPI:
    """Test the Axum REST API server."""

    @pytest.mark.asyncio
    async def test_health_check(self, axum_client):
        """Health endpoint should return status and timestamp."""
        health = await health_get.asyncio(client=axum_client)
        assert health.status == "ok"
        assert health.checked_at is not None
        assert health.region == "us-east-1"

    @pytest.mark.asyncio
    async def test_list_users(self, axum_client):
        """Users list should return array of users."""
        users = await users_list.asyncio(client=axum_client)
        assert isinstance(users, list)
        assert len(users) > 0
        
        user = users[0]
        assert hasattr(user, 'id')
        assert hasattr(user, 'username')
        assert hasattr(user, 'email')

    @pytest.mark.asyncio
    async def test_get_existing_user(self, axum_client):
        """Getting existing user should return user data."""
        # First, ensure we have users by listing them
        users = await users_list.asyncio(client=axum_client)
        assert len(users) > 0, "No users found - server may not be initialized"
        
        # Get the first user's ID
        first_user_id = users[0].id
        
        # Test getting that specific user
        user = await user_get.asyncio(client=axum_client, id=first_user_id)
        assert user.id == first_user_id
        assert user.username is not None
        assert user.email is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, axum_client):
        """Getting nonexistent user should return 404 with error."""
        # Use a very high ID that's unlikely to exist
        nonexistent_id = 999999
        response = await user_get.asyncio_detailed(client=axum_client, id=nonexistent_id)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert isinstance(response.parsed, ApiError)
        assert response.parsed.code == "user_not_found"
        assert str(nonexistent_id) in response.parsed.message

    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, axum_client):
        """Creating duplicate user should return 409 conflict."""
        # First get the list of existing users to find one to duplicate
        users = await users_list.asyncio(client=axum_client)
        assert len(users) > 0, "No users found - server may not be initialized"
        
        # Use the first existing user for duplication test
        existing_user = users[0]
        request = CreateUserRequest(
            username=existing_user.username,
            email=existing_user.email,
            roles=[Role.ADMIN],
            timezone="UTC",
        )
        
        response = await user_create.asyncio_detailed(client=axum_client, body=request)
        assert response.status_code == HTTPStatus.CONFLICT
        assert isinstance(response.parsed, ApiError)
        assert "already exists" in response.parsed.message


class TestReflectAPI:
    """Test the ReflectAPI RPC server."""

    @pytest.mark.asyncio
    async def test_health_check(self, reflect_client):
        """Health operation should return status and timestamp."""
        response = await reflect_client.health.get()
        assert response.data is not None
        
        health = response.data
        status = health.get("status") if isinstance(health, dict) else getattr(health, "status", None)
        assert status == "ok"

    @pytest.mark.asyncio
    async def test_list_users(self, reflect_client):
        """Users list operation should return array of users."""
        response = await reflect_client.users.list()
        assert response.data is not None
        
        users = response.data
        assert isinstance(users, list)
        assert len(users) > 0
        
        user = users[0]
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
        assert user_id is not None
        assert username is not None

    @pytest.mark.asyncio
    async def test_get_existing_user_manual(self, reflect_client):
        """Getting existing user via manual API call should work."""
        # First get the list of users to find an existing one
        users_response = await reflect_client.users.list()
        assert users_response.data is not None
        users = users_response.data
        assert len(users) > 0, "No users found - server may not be initialized"
        
        # Use the first user's ID for testing
        first_user = users[0]
        first_user_id = first_user.get("id") if isinstance(first_user, dict) else getattr(first_user, "id")
        
        async with httpx.AsyncClient() as client:
            response = await client.post("http://127.0.0.1:9000/user.get", json={"id": first_user_id})
            assert response.status_code == 200
            
            user_data = response.json()
            assert user_data["id"] == first_user_id
            assert "username" in user_data
            assert "email" in user_data

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_manual(self):
        """Getting nonexistent user should return error."""
        async with httpx.AsyncClient() as client:
            response = await client.post("http://127.0.0.1:9000/user.get", json={"id": 9999})
            assert response.status_code == 404
            
            error_data = response.json()
            assert "code" in error_data
            assert "message" in error_data
            assert "9999" in error_data["message"]

    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, reflect_client):
        """Creating duplicate user should return conflict error."""
        # First get the list of existing users to find one to duplicate
        users_response = await reflect_client.users.list()
        assert users_response.data is not None
        users = users_response.data
        assert len(users) > 0, "No users found - server may not be initialized"
        
        # Use the first existing user for duplication test
        existing_user = users[0]
        existing_username = existing_user.get("username") if isinstance(existing_user, dict) else getattr(existing_user, "username")
        existing_email = existing_user.get("email") if isinstance(existing_user, dict) else getattr(existing_user, "email")
        
        request = SharedModelsCreateUserRequest(
            username=existing_username,
            email=existing_email,
            roles=[SharedModelsRole.ADMIN],
            timezone="UTC",
        )
        
        with pytest.raises(Exception) as exc_info:
            await reflect_client.user.create(data=request)
        
        error_str = str(exc_info.value)
        assert "409" in error_str and "user_exists" in error_str


class TestAPIConsistency:
    """Test that both APIs return consistent data."""

    @pytest.mark.asyncio
    async def test_health_consistency(self, axum_client, reflect_client):
        """Both APIs should return the same health status."""
        # Get health from both APIs
        axum_health = await health_get.asyncio(client=axum_client)
        reflect_response = await reflect_client.health.get()
        reflect_health = reflect_response.data
        
        # Extract status
        axum_status = axum_health.status
        reflect_status = (reflect_health.get("status") if isinstance(reflect_health, dict) 
                         else getattr(reflect_health, "status", None))
        
        assert axum_status == reflect_status == "ok"

    @pytest.mark.asyncio
    async def test_user_count_consistency(self, axum_client, reflect_client):
        """Both APIs should return the same number of users."""
        axum_users = await users_list.asyncio(client=axum_client)
        reflect_response = await reflect_client.users.list()
        reflect_users = reflect_response.data
        
        assert len(axum_users) == len(reflect_users)

    @pytest.mark.asyncio
    async def test_user_data_consistency(self, axum_client):
        """User data should be consistent between APIs."""
        # First get the list of users to find an existing one
        axum_users = await users_list.asyncio(client=axum_client)
        assert len(axum_users) > 0, "No users found - server may not be initialized"
        
        # Use the first user's ID for consistency testing
        first_user_id = axum_users[0].id
        
        # Get user from Axum API
        axum_user = await user_get.asyncio(client=axum_client, id=first_user_id)
        
        # Get user from ReflectAPI via manual call
        async with httpx.AsyncClient() as client:
            response = await client.post("http://127.0.0.1:9000/user.get", json={"id": first_user_id})
            reflect_user = response.json()
        
        # Compare key fields
        assert axum_user.id == reflect_user["id"]
        assert axum_user.username == reflect_user["username"]
        assert axum_user.email == reflect_user["email"]