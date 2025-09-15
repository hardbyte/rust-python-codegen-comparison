import asyncio

from reflect_api_demo_client import Client
from reflect_api_demo_client.api.default import message_get, users_list, user_create
from reflect_api_demo_client.models import reflect_server_proto_create_user_request
from reflect_api_demo_client.types import Response


async def main() -> None:
    """Use the generated reflectapi client."""
    client = Client(base_url="http://127.0.0.1:9000")

    print("=== Testing ReflectAPI Server ===")

    # Test 1: Get message
    print("\n1. Getting message...")
    message_response = await message_get.asyncio_detailed(client=client)
    if message_response.status_code == 200:
        message = message_response.parsed
        if message:
            print(f"Message: {message.text} (at {message.timestamp})")
        else:
            print("No message data received")
    else:
        print(f"Error getting message: {message_response.status_code}")

    # Test 2: List users
    print("\n2. Listing users...")
    users_response = await users_list.asyncio_detailed(client=client)
    if users_response.status_code == 200:
        users = users_response.parsed
        if users:
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  - {user.username} ({user.email}) - Active: {user.active}")
        else:
            print("No users found")
    else:
        print(f"Error listing users: {users_response.status_code}")

    # Test 3: Create a new user
    print("\n3. Creating new user...")
    create_request = reflect_server_proto_create_user_request.ReflectServerProtoCreateUserRequest(
        username="charlie",
        email="charlie@example.com"
    )

    create_response = await user_create.asyncio_detailed(
        client=client,
        body=create_request
    )

    if create_response.status_code == 200:
        new_user = create_response.parsed
        if new_user:
            print(f"Created user: {new_user.username} (ID: {new_user.id}, Email: {new_user.email})")
        else:
            print("User created but no data returned")
    else:
        print(f"Error creating user: {create_response.status_code}")
        if create_response.content:
            print(f"Error content: {create_response.content}")

    # Test 4: List users again to see the new user
    print("\n4. Listing users after creation...")
    users_response2 = await users_list.asyncio_detailed(client=client)
    if users_response2.status_code == 200:
        users = users_response2.parsed
        if users:
            print(f"Now found {len(users)} users:")
            for user in users:
                print(f"  - {user.username} ({user.email}) - Active: {user.active}")
        else:
            print("No users found")
    else:
        print(f"Error listing users: {users_response2.status_code}")


if __name__ == "__main__":
    asyncio.run(main())