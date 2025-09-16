# Rust ↔ Python Codegen Demo

This repository compares two approaches for delivering the same API surface from Rust to Python:

- **`shared_models/`** – a lightweight crate that defines all DTOs/enums once and conditionally derives `utoipa` and `reflectapi` traits so each server emits the same schema.
- **`axum_server/`** – an Axum application annotated with [`utoipa`](https://docs.rs/utoipa) that exposes REST endpoints and an OpenAPI document at runtime.
- **`reflect_server/`** – a code-first [`reflectapi`](https://crates.io/crates/reflectapi) service that builds an identical schema and streams the specification as both Reflect JSON and OpenAPI.
- **Generated clients** – `axum-server-client/` and `reflect-api-demo-client/` are regenerated automatically by `./test-ci.sh` so that the Python examples always match the latest schema.

By sharing the types the two servers emit byte-identical payloads while covering richer features: timestamps (`chrono::DateTime<Utc>`), enums, optional fields, and structured error payloads.

## API Surface

### REST API (Axum + utoipa)

| Method | Path          | Description                     |
|--------|---------------|---------------------------------|
| GET    | `/health`     | Health check with timestamp     |
| GET    | `/users`      | List all users                  |
| GET    | `/users/{id}` | Fetch a single user by id       |
| POST   | `/users`      | Create a user with validation   |

All error responses use `{ "code": string, "message": string, "detail"?: string }` and appropriate HTTP status codes.

### RPC API (ReflectAPI)

| Operation     | Route         | HTTP Methods | Notes                                      |
|---------------|---------------|--------------|-------------------------------------------|
| `health.get`  | `/health.get` | GET, POST    | Same payload as the REST `/health` route |
| `users.list`  | `/users.list` | GET, POST    | Enumerates users                          |
| `user.get`    | `/user.get`   | POST         | Accepts `{ "id": number }`               |
| `user.create` | `/user.create`| POST         | Validates username/email/roles           |

**HTTP Method Support:**
- Operations without parameters (`health.get`, `users.list`): Support both GET and POST
- Operations with parameters (`user.get`, `user.create`): POST only with JSON request body

The generated OpenAPI document is normalized so that enums appear as standard `enum` values, keeping the Python generator happy.

### Shared data types

- `User`
  - `id: u64`
  - `username`, `email`
  - `created_at: DateTime<Utc>`
  - `roles: [admin|editor|viewer]`
  - `status: [active|invited|suspended]`
  - `preferences?: { theme, timezone?, last_login_at? }`
- `HealthStatus`
  - `status`
  - `checked_at: DateTime<Utc>`
  - `region?`
- `ApiError`
  - `code`, `message`, `detail?`
- `CreateUserRequest`
  - `username`, `email`
  - `roles?`, `timezone?`

These types are reused verbatim in both the utoipa and reflectapi servers.

## End-to-End Workflow

1. **Install prerequisites**
   - Rust (stable channel)
   - Python 3.12+
   - [`uv`](https://github.com/astral-sh/uv)

2. **Run the local CI harness**
   ```bash
   ./test-ci.sh
   ```
   The script:
   - Runs `cargo fmt` + `cargo clippy`
   - Builds both servers in release mode
   - Boots the binaries and waits for readiness
   - Downloads and normalizes the OpenAPI specs
   - Regenerates the Python clients with `openapi-python-client`
   - Runs the Python examples and test suite to verify functionality

3. **Start servers manually**
   ```bash
   # Start Axum/utoipa server (port 8000)
   cargo run --release --bin axum_server

   # Start ReflectAPI server (port 9000)
   cargo run --release --bin reflect_server
   ```

4. **Generate Python clients manually**
   ```bash
   # Generate client for Axum REST API
   uv run openapi-python-client generate --url http://127.0.0.1:8000/api-docs/openapi.json --meta uv --overwrite

   # Generate client for ReflectAPI Server (using git version with Python support)
   cargo install --git https://github.com/thepartly/reflectapi reflectapi-cli
   reflectapi codegen --language python --schema reflect_server/reflectapi.json \
     --output reflect-api-demo-client/reflect_api_demo_client \
     --python-package-name "reflect_api_demo_client" --python-async
   ```

5. **Initialize the uv workspace and run Python demos**
   ```bash
   # Sync workspace dependencies (creates proper local package links)
   uv sync

   # Run simple examples
   uv run python axum_example.py      # REST API simple example
   uv run python reflect_example.py   # RPC API simple example

   # Run interactive TUI demo for presentations
   uv run python demo_tui.py          # Manual control (default)
   uv run python demo_tui.py --auto   # Auto-advance mode

   # Run test suite
   uv run pytest test_apis.py -v
   ```

The `test-ci.sh` pipeline mirrors the `.github/workflows/ci.yml` job so GitHub Actions and local development stay in sync.

## Repository Layout

```
├── shared_models/               # Reusable Rust crate with DTOs/enums
├── axum_server/                 # Axum + utoipa server (REST API)
│   └── src/
│       └── main.rs              # Routes, handlers, OpenAPI doc
├── reflect_server/              # reflectapi builder + Axum host (RPC API)
│   └── src/
│       ├── lib.rs               # Builder using shared models with tags
│       └── main.rs              # Spec export + Axum bridge
├── axum-server-client/          # Generated OpenAPI client for REST server (workspace member)
│   └── pyproject.toml           # Modern pyproject.toml for uv
├── reflect-api-demo-client/     # Generated OpenAPI client for RPC server (workspace member)
│   └── pyproject.toml           # Modern pyproject.toml for uv
├── axum_example.py              # Simple example client for REST API
├── reflect_example.py           # Simple example client for RPC API
├── demo_tui.py                  # Interactive TUI demo for presentations
├── test_apis.py                 # Pytest test suite for both APIs
├── pyproject.toml               # uv workspace root with local dependencies
├── test-ci.sh                   # Local CI + codegen harness
└── .github/workflows/ci.yml     # GitHub Actions workflow that runs the same script
```

## Notes

- Both servers emit Swagger/Redoc UIs (`http://127.0.0.1:8000/swagger-ui`, `http://127.0.0.1:9000/doc`).
- The reflectapi server writes `reflect_server/reflectapi.json` on startup; `test-ci.sh` waits for the file before generating clients.
- Enums, timestamps, optional fields, and structured errors are now first-class in both ecosystems, so the generated Python clients expose type-safe enums and `datetime` values.
- If you tweak the schema, rerun `./test-ci.sh` to refresh the Python clients and validate the system end-to-end.
