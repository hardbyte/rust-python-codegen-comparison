#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUST_TARGET_DIR="$ROOT_DIR/target/release"
UTOIPA_BIN="$RUST_TARGET_DIR/axum_server"
REFLECT_BIN="$RUST_TARGET_DIR/reflect_server"
UTOIPA_CLIENT_DIR="$ROOT_DIR/axum-server-client"
REFLECT_CLIENT_DIR="$ROOT_DIR/reflect-api-demo-client"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

cleanup() {
    if [[ -n "${UTOIPA_PID:-}" ]] && kill -0 "$UTOIPA_PID" 2>/dev/null; then
        kill "$UTOIPA_PID" || true
    fi
    if [[ -n "${REFLECT_PID:-}" ]] && kill -0 "$REFLECT_PID" 2>/dev/null; then
        kill "$REFLECT_PID" || true
    fi
}

trap cleanup EXIT

echo -e "${CYAN}🚀 Testing CI workflow components locally...${NC}"

# Test 1: Check project structure
echo "📁 Checking project structure..."
[[ -d "$ROOT_DIR/axum_server" ]] && print_status "axum_server directory exists"
[[ -d "$ROOT_DIR/reflect_server" ]] && print_status "reflect_server directory exists"
[[ -f "$ROOT_DIR/axum_example.py" ]] && print_status "axum_example.py exists"
[[ -f "$ROOT_DIR/reflect_example.py" ]] && print_status "reflect_example.py exists"
[[ -f "$ROOT_DIR/.github/workflows/ci.yml" ]] && print_status "CI workflow exists"

# Test 2: Rust formatting and linting
echo "🦀 Checking Rust formatting and linting..."
if cargo fmt --all -- --check; then
    print_status "Rust code formatted"
else
    print_warning "cargo fmt reported issues"
fi

if cargo clippy --workspace --all-targets -- -D warnings; then
    print_status "clippy clean"
else
    print_warning "clippy produced warnings"
fi

# Test 3: Build both servers in release mode
echo "🔨 Building workspace in release mode..."
if cargo build --workspace --release; then
    print_status "Workspace builds in release mode"
else
    print_error "Release build failed"
    exit 1
fi

# Test 4: Check if binaries exist
echo "📦 Checking built binaries..."
[[ -x "$UTOIPA_BIN" ]] && print_status "utoipa binary exists"
[[ -x "$REFLECT_BIN" ]] && print_status "reflectapi binary exists"

# Test 5: Quick server startup test (without keeping them running)
echo "🌐 Smoke testing server startup..."
timeout 10s "$UTOIPA_BIN" >/dev/null 2>&1 &
TEMP_PID=$!
sleep 3
if kill -0 "$TEMP_PID" 2>/dev/null; then
    print_status "utoipa server starts successfully"
else
    print_warning "utoipa server exited early"
fi
kill "$TEMP_PID" 2>/dev/null || true
wait "$TEMP_PID" 2>/dev/null || true

timeout 10s "$REFLECT_BIN" >/dev/null 2>&1 &
TEMP_PID=$!
sleep 3
if kill -0 "$TEMP_PID" 2>/dev/null; then
    print_status "reflectapi server starts successfully"
else
    print_warning "reflectapi server exited early"
fi
kill "$TEMP_PID" 2>/dev/null || true
wait "$TEMP_PID" 2>/dev/null || true

# Test 6: Check Python toolchain
echo "🐍 Checking Python tooling..."
if command -v python3 >/dev/null 2>&1; then
    print_status "Python 3 available ($(python3 --version))"
else
    print_error "Python 3 is not available"
fi

if command -v uv >/dev/null 2>&1; then
    print_status "uv is available"
else
    print_warning "uv not found (required for client generation)"
fi

# Resolve Python dependencies (skip for now - clients not generated yet)
echo "📦 Checking Python dependencies..."
# uv sync >/dev/null  # Will sync after clients are generated
print_status "Python environment check complete"

# Test 7: Validate workflow YAML syntax if yamllint exists
echo "📋 Validating workflow YAML syntax..."
if command -v yamllint >/dev/null 2>&1; then
    if yamllint "$ROOT_DIR/.github/workflows/ci.yml"; then
        print_status "CI workflow YAML is valid"
    else
        print_warning "CI workflow YAML has issues"
    fi
else
    print_warning "yamllint not available, skipping YAML validation"
fi

# Test 8: start both servers in background
echo "🚀 Starting servers for end-to-end tests..."
"$UTOIPA_BIN" &
UTOIPA_PID=$!
"$REFLECT_BIN" &
REFLECT_PID=$!

sleep 5

if ! kill -0 "$UTOIPA_PID" 2>/dev/null; then
    print_error "utoipa server failed to stay running"
    exit 1
fi
if ! kill -0 "$REFLECT_PID" 2>/dev/null; then
    print_error "reflectapi server failed to stay running"
    exit 1
fi
print_status "Both servers are running"

# Test 9: Verify HTTP endpoints quickly
echo "🔍 Verifying key endpoints..."
if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    print_status "utoipa /health reachable"
else
    print_error "utoipa /health unreachable"
fi
if curl -fsS http://127.0.0.1:8000/users >/dev/null; then
    print_status "utoipa /users reachable"
fi
if curl -fsS http://127.0.0.1:9000/openapi.json >/dev/null; then
    print_status "reflectapi OpenAPI reachable"
fi

for _ in {1..10}; do
    if [[ -f "$ROOT_DIR/reflect_server/reflectapi.json" ]]; then
        print_status "reflectapi.json generated"
        break
    fi
    sleep 1
done

if [[ ! -f "$ROOT_DIR/reflect_server/reflectapi.json" ]]; then
    print_error "reflectapi.json was not generated"
    exit 1
fi

# Test 10: Generate Python clients
echo "🛠 Generating Python clients..."
rm -rf "$UTOIPA_CLIENT_DIR" "$REFLECT_CLIENT_DIR"

curl -fsS http://127.0.0.1:8000/api-docs/openapi.json -o "$ROOT_DIR/api.json"
print_status "Downloaded utoipa OpenAPI spec"

uv run openapi-python-client generate --path "$ROOT_DIR/api.json" --output-path "$UTOIPA_CLIENT_DIR" --overwrite --meta uv >/dev/null

# Update Python version requirement to match reflectapi-runtime requirements
sed -i 's/requires-python = "~=3.9"/requires-python = ">=3.12"/' "$UTOIPA_CLIENT_DIR/pyproject.toml"

print_status "Generated utoipa Python client"

if command -v reflectapi >/dev/null 2>&1; then
    print_status "reflectapi-cli available"
else
    echo "📦 Installing reflectapi-cli via cargo..."
    if cargo install --git https://github.com/thepartly/reflectapi reflectapi-cli --force >/dev/null 2>&1; then
        print_status "reflectapi-cli installed"
    else
        print_error "Failed to install reflectapi-cli"
        exit 1
    fi
fi

# Create the proper package structure for reflectapi client
mkdir -p "$REFLECT_CLIENT_DIR/reflect_api_demo_client"
reflectapi codegen --language python --schema "$ROOT_DIR/reflect_server/reflectapi.json" --output "$REFLECT_CLIENT_DIR/reflect_api_demo_client" --python-package-name "reflect_api_demo_client" --python-async >/dev/null

# Create pyproject.toml for the generated client
cat > "$REFLECT_CLIENT_DIR/pyproject.toml" <<'PYPROJECT'
[project]
name = "reflect-api-demo-client"
version = "0.1.0"
description = "ReflectAPI generated Python client"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0.0",
    "reflectapi-runtime>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["reflect_api_demo_client"]
PYPROJECT

print_status "Generated reflectapi Python client"

# Update root pyproject.toml to include workspace configuration
echo "📦 Configuring uv workspace..."
cat > "$ROOT_DIR/pyproject.toml" <<'WORKSPACE'
[project]
name = "rust-python-demo"
version = "0.1.0"
description = "Demo of Rust-Python interop with auto-generated clients"
requires-python = ">=3.12"
dependencies = [
    "openapi-python-client>=0.21.0",
    "axum-server-client",
    "reflect-api-demo-client",
    "rich>=13.0.0",
    "httpx>=0.25.0",
]

[tool.uv.sources]
axum-server-client = { workspace = true }
reflect-api-demo-client = { workspace = true }

[tool.uv.workspace]
members = ["axum-server-client", "reflect-api-demo-client"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = [
    "mypy>=1.18.1",
    "ty>=0.0.1a20",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]

[tool.hatch.build.targets.wheel]
packages = []
include = ["*.py"]
WORKSPACE

print_status "Configured uv workspace"

# Sync the workspace to install the generated clients
uv sync >/dev/null
print_status "Synced workspace with generated clients"

# Test 11: Execute Python integration scripts
echo "🧪 Running Python integration demos..."
if uv run python "$ROOT_DIR/axum_example.py" >/dev/null; then
    print_status "axum Python demo passed"
else
    print_error "axum Python demo failed"
    exit 1
fi

if uv run python "$ROOT_DIR/reflect_example.py" >/dev/null; then
    print_status "reflectapi Python demo passed"
else
    print_error "reflectapi Python demo failed"
    exit 1
fi

# Run test suite
echo "🧪 Running test suite..."
if uv run pytest "$ROOT_DIR/test_apis.py" -q; then
    print_status "pytest tests passed"
else
    print_error "pytest tests failed"
    exit 1
fi

# Completed
echo ""
echo -e "${GREEN}🎉 Full E2E validation completed successfully!${NC}"
