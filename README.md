# Rust-Python Interop Demo

This project demonstrates seamless interoperability between Rust and Python using OpenAPI code generation. A Rust HTTP server generates OpenAPI specifications, which are then used to automatically generate a type-safe Python client.

## Project Structure

```
├── rust_server/          # Rust HTTP server with OpenAPI generation
│   ├── src/
│   │   ├── main.rs        # Main server with utoipa annotations
│   │   └── models.rs      # Data models with OpenAPI schemas
│   └── Cargo.toml         # Rust dependencies
├── my_client/             # Generated Python client (auto-generated)
├── main.py                # Python client usage example
├── api.json               # Downloaded OpenAPI specification
└── .venv/                 # Python virtual environment
```

## Features

- **Rust HTTP Server**: Built with Axum framework
- **OpenAPI Generation**: Automatic spec generation using utoipa
- **Swagger UI**: Interactive API documentation at `/swagger-ui`
- **Python Client Generation**: Type-safe client with attrs models
- **Full Type Safety**: End-to-end type safety from Rust to Python

## Getting Started

### Prerequisites

- Rust (latest stable)
- Python 3.12+
- uv (Python package manager)

### 1. Run the Rust Server

```bash
cd rust_server
cargo run
```

The server will start on `http://127.0.0.1:8000` with:
- API endpoint: `GET /user`
- Swagger UI: `http://127.0.0.1:8000/swagger-ui`
- OpenAPI spec: `http://127.0.0.1:8000/api-docs/openapi.json`

### 2. Generate the Python Client

With the server running, download the OpenAPI spec and generate the client:

```bash
# Download the OpenAPI specification
curl http://127.0.0.1:8000/api-docs/openapi.json -o api.json

# Set up Python environment
uv venv
source .venv/bin/activate

# Install the generator
uv pip install openapi-python-client

# Generate the Python client
openapi-python-client generate --path api.json --output-path ./my_client

# Install the generated client
uv pip install ./my_client/
```

### 3. Use the Python Client

```bash
# Run the example
python main.py
```

## Example Usage

The generated Python client provides full type safety and IDE autocompletion:

```python
import asyncio
from my_client.rust_server_client import Client
from my_client.rust_server_client.api.crate import get_user

async def main():
    client = Client(base_url="http://127.0.0.1:8000")

    # Type-safe API call
    user_response = await get_user.asyncio_detailed(client=client)

    if user_response.status_code == 200:
        user = user_response.parsed
        print(f"User: {user.username} (ID: {user.id})")
        # IDE will provide full autocompletion for user.username and user.id

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Benefits

1. **Type Safety**: Changes to Rust models automatically propagate to Python
2. **Code Generation**: No manual client writing required
3. **IDE Support**: Full autocompletion and type checking in Python
4. **Documentation**: Automatic API documentation via Swagger UI
5. **Validation**: Client-side validation based on OpenAPI schema

## Development Workflow

1. Modify Rust models or API endpoints
2. Restart the Rust server
3. Re-download the OpenAPI spec
4. Regenerate the Python client
5. Python code automatically benefits from type updates

This approach ensures that breaking changes in the API are caught at compile/type-check time rather than runtime.