#!/usr/bin/env python3
"""Simple example client for the Axum REST API server."""

import asyncio
from http import HTTPStatus

from axum_server_client import Client
from axum_server_client.api.users import health_get, user_create, user_get, users_list
from axum_server_client.models import CreateUserRequest, Role


async def main() -> None:
    """Demonstrate basic usage of the Axum REST API."""
    client = Client(base_url="http://127.0.0.1:8000")

    # Health check
    health = await health_get.asyncio(client=client)
    print(f"Health: {health.status} at {health.checked_at}")

    # List users
    users = await users_list.asyncio(client=client)
    print(f"Found {len(users)} users:")
    for user in users:
        roles = [role.value for role in user.roles] if user.roles else []
        print(f"  #{user.id}: {user.username} ({', '.join(roles)})")

    # Get specific user
    user = await user_get.asyncio(client=client, id=1)
    print(f"User #1: {user.username} <{user.email}>")

    # Create new user (idempotent)
    request = CreateUserRequest(
        username="example",
        email="example@test.com",
        roles=[Role.VIEWER],
        timezone="UTC",
    )
    
    response = await user_create.asyncio_detailed(client=client, body=request)
    if response.status_code == HTTPStatus.CREATED:
        new_user = response.parsed
        print(f"Created user #{new_user.id}: {new_user.username}")
    elif response.status_code == HTTPStatus.CONFLICT:
        print("User already exists")
    else:
        print(f"Unexpected response: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(main())