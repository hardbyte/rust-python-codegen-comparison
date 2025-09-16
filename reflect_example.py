#!/usr/bin/env python3
"""Simple example client for the ReflectAPI server."""

import asyncio

from reflect_api_demo_client import AsyncClient
from reflect_api_demo_client.generated import (
    ReflectServerGetUserRequest,
    SharedModelsCreateUserRequest,
    SharedModelsRole,
)


async def main() -> None:
    """Demonstrate basic usage of the ReflectAPI server."""
    client = AsyncClient(base_url="http://127.0.0.1:9000")

    # Health check
    health_response = await client.health.get()
    if health_response.data:
        health = health_response.data
        status = health.get("status") if isinstance(health, dict) else getattr(health, "status", "unknown")
        print(f"Health: {status}")

    # List users
    users_response = await client.users.list()
    if users_response.data:
        users = users_response.data
        print(f"Found {len(users)} users:")
        for user in users:
            user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", "?")
            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", "?")
            roles = user.get("roles", []) if isinstance(user, dict) else getattr(user, "roles", [])
            roles_str = ", ".join(str(r) for r in roles) if roles else "none"
            print(f"  #{user_id}: {username} ({roles_str})")

    # Get specific user
    request = ReflectServerGetUserRequest(id=1)
    user_response = await client.user.get(data=request)
    if user_response.data:
        user_data = user_response.data
        username = user_data.get("username") if isinstance(user_data, dict) else getattr(user_data, "username", "?")
        email = user_data.get("email") if isinstance(user_data, dict) else getattr(user_data, "email", "?")
        print(f"User #1: {username} <{email}>")

    # Create new user (idempotent)
    request = SharedModelsCreateUserRequest(
        username="example_rpc",
        email="example_rpc@test.com",
        roles=[SharedModelsRole.VIEWER],
        timezone="UTC",
    )
    
    try:
        created = await client.user.create(data=request)
        if created.data:
            user = created.data
            user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", "?")
            username = user.get("username") if isinstance(user, dict) else getattr(user, "username", "?")
            print(f"Created user #{user_id}: {username}")
    except Exception as e:
        if "409" in str(e) and "user_exists" in str(e):
            print("User already exists")
        else:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())