# Rust-Python Interop Demo

This project demonstrates seamless interoperability between Rust and Python using OpenAPI code generation. It showcases two different approaches:

1. **utoipa** - Direct OpenAPI generation with Swagger UI
2. **reflectapi** - Code-first API definition with multi-language client generation

Both Rust servers generate OpenAPI specifications that are used to automatically generate type-safe Python clients.

## Project Structure

```
├── rust_server/               # Rust HTTP server with utoipa
│   ├── src/
│   │   ├── main.rs           # Main server with utoipa annotations
│   │   └── models.rs         # Data models with OpenAPI schemas
│   └── Cargo.toml            # Rust dependencies
├── reflect_server/           # Rust HTTP server with reflectapi
│   ├── src/
│   │   ├── main.rs           # Main server entry point
│   │   └── lib.rs            # API definition with reflectapi
│   └── Cargo.toml            # Rust dependencies with reflectapi
├── my_client/                # Generated Python client for utoipa server
├── reflect_api_demo_client/  # Generated Python client for reflectapi server
├── main.py                   # Python client usage example (utoipa)
├── reflect_main.py           # Python client usage example (reflectapi)
├── api.json                  # Downloaded OpenAPI spec (utoipa)
├── reflectapi_spec.json      # Downloaded OpenAPI spec (reflectapi)
└── .venv/                    # Python virtual environment
```

## Features

### utoipa Server (Port 8000)
- **Simple Setup**: Attribute-based OpenAPI generation
- **Swagger UI**: Interactive documentation at `/swagger-ui`
- **Direct HTTP**: Traditional REST API with JSON responses
- **Minimal Dependencies**: Just utoipa + axum

### reflectapi Server (Port 9000)
- **Code-First**: Define API through Rust functions
- **Rich Type System**: Support for complex Rust types
- **Multi-Language**: Generate clients in TypeScript, Rust, Python
- **Advanced Features**: Error handling, validation, state management

## Getting Started

### Prerequisites

- Rust (latest stable)
- Python 3.12+
- uv (Python package manager)

### 1. Run Both Rust Servers

**Start the utoipa server (port 8000):**
```bash
cd rust_server
cargo run
```

**Start the reflectapi server (port 9000):**
```bash
cd reflect_server
cargo run
```

Servers will be available at:
- utoipa: `http://127.0.0.1:8000` with Swagger UI at `/swagger-ui`
- reflectapi: `http://127.0.0.1:9000` with Swagger UI at `/swagger-ui`

### 2. Generate Python Clients

**Setup Python environment:**
```bash
uv venv
source .venv/bin/activate
uv pip install openapi-python-client
```

**Generate utoipa client:**
```bash
curl http://127.0.0.1:8000/api-docs/openapi.json -o api.json
openapi-python-client generate --path api.json --output-path ./my_client
uv pip install ./my_client/
```

**Generate reflectapi client:**
```bash
curl http://127.0.0.1:9000/openapi.json -o reflectapi_spec.json
openapi-python-client generate --path reflectapi_spec.json --output-path ./reflect_client
uv pip install ./reflect_client/
```

### 3. Use the Python Clients

**Test utoipa client:**
```bash
python main.py
```

**Test reflectapi client:**
```bash
python reflect_main.py
```

## API Comparison

### utoipa Server Features
- Simple user model with id, username
- Single GET endpoint: `/user`
- Minimal setup, fast iteration

### reflectapi Server Features
- Rich user model with id, username, email, active status
- Multiple endpoints:
  - `message.get` - Get a simple message
  - `users.list` - List all users
  - `user.create` - Create new users with validation
- State management with in-memory storage
- Error handling with typed errors

## Example Usage

### utoipa Client
```python
from my_client.rust_server_client import Client
from my_client.rust_server_client.api.crate import get_user

client = Client(base_url="http://127.0.0.1:8000")
user_response = await get_user.asyncio_detailed(client=client)
user = user_response.parsed
print(f"User: {user.username} (ID: {user.id})")
```

### reflectapi Client
```python
from reflect_api_demo_client import Client
from reflect_api_demo_client.api.default import users_list, user_create
from reflect_api_demo_client.models import reflect_server_proto_create_user_request

client = Client(base_url="http://127.0.0.1:9000")

# List users
users_response = await users_list.asyncio_detailed(client=client)
users = users_response.parsed

# Create user
create_request = reflect_server_proto_create_user_request.ReflectServerProtoCreateUserRequest(
    username="newuser",
    email="newuser@example.com"
)
create_response = await user_create.asyncio_detailed(client=client, body=create_request)
```

## Key Benefits

1. **Type Safety**: Changes to Rust models automatically propagate to Python
2. **Code Generation**: No manual client writing required
3. **IDE Support**: Full autocompletion and type checking in Python
4. **Documentation**: Automatic API documentation via Swagger UI
5. **Validation**: Client-side validation based on OpenAPI schema
6. **Multiple Approaches**: Choose between simple (utoipa) or feature-rich (reflectapi)

## Development Workflow

### For utoipa:
1. Modify Rust models or API endpoints with utoipa annotations
2. Restart the Rust server
3. Re-download the OpenAPI spec from `/api-docs/openapi.json`
4. Regenerate the Python client
5. Python code automatically benefits from type updates

### For reflectapi:
1. Modify Rust API definitions in the builder
2. Restart the Rust server
3. Re-download the OpenAPI spec from `/openapi.json`
4. Regenerate the Python client
5. Python code automatically benefits from type updates

This approach ensures that breaking changes in the API are caught at compile/type-check time rather than runtime.

## When to Use Which

**Choose utoipa when:**
- Building simple REST APIs
- Want minimal setup overhead
- Need quick prototyping
- Working with existing axum applications

**Choose reflectapi when:**
- Building complex APIs with rich types
- Need multi-language client generation
- Want code-first API design
- Need advanced error handling and validation
- Working with complex Rust type systems