import asyncio

from my_client.rust_server_client import Client
from my_client.rust_server_client.models import User
from my_client.rust_server_client.types import Response
from my_client.rust_server_client.api.crate import get_user


async def main() -> None:
    """Use the generated client."""
    client = Client(base_url="http://127.0.0.1:8000")

    user_response = await get_user.asyncio_detailed(client=client)

    if user_response.status_code == 200:
        user = user_response.parsed
        if user:
            print(f"Success! Got user: {user.username} (ID: {user.id})")
        else:
            print("Error: No user data in response")
    else:
        print(f"Error: {user_response.status_code}")
        print(user_response.content)


if __name__ == "__main__":
    asyncio.run(main())