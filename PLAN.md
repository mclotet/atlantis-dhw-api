# PLAT-057: Refactor atlantis-dhw-api

## Context

The DHW API is a single-file FastAPI service that queries InfluxDB to expose domestic hot water status. It pre-dates Atlantis standards: it uses standard Python logging (audit finding C-04), has no Pydantic models, hardcodes InfluxDB field names, and has no tests.

This refactor restructures it as a **hexagonal (ports & adapters) architecture** — the same pattern used in `atlantis-forge` — and brings it into full compliance with the Atlantis Logging Standard v0.2 and Python Services Standard v0.1.

**Prerequisite completed:** CORE-014 — `BaseServiceSettings` is now in `atlantis-core`.

**Reference implementations:**

- Hexagonal pattern: `atlantis-forge/backend/forge/`
- Config pattern: `python-services.md` v0.1 + `atlantis-core/python/atlantis_core/config.py`

---

## Progress Tracker

Track completion during implementation sessions. Update ☐ → ✅ as each step is done.

| # | Step | Status |
| --- | --- | --- |
| 1 | Write this plan into the repo as `PLAN.md` with the tracker | ✅ |
| 2 | `pyproject.toml` — update build backend, Python version, deps | ✅ |
| 3 | `atlantis.toml` — new file, service identity | ✅ |
| 4 | `.env.example` — trim to secrets only | ✅ |
| 5 | `app/domain/models.py` — domain entities | ✅ |
| 6 | `app/domain/exceptions.py` — domain exceptions | ✅ |
| 7 | `app/ports/influx_port.py` — abstract InfluxDB port | ✅ |
| 8 | `app/application/dhw_service.py` — use case functions | ✅ |
| 9 | `app/adapters/influx/influx_adapter.py` — concrete InfluxDB adapter | ✅ |
| 10 | `app/adapters/api/schemas.py` — Pydantic request/response schemas | ✅ |
| 11 | `app/adapters/api/deps.py` — DI wiring | ✅ |
| 12 | `app/adapters/api/routers/dhw.py` — GET /dhw route | ✅ |
| 13 | `app/adapters/api/main.py` — FastAPI app, lifespan, /health, exception handler | ✅ |
| 14 | `app/config.py` — Settings subclass | ✅ |
| 15 | `tests/conftest.py` — fixtures | ✅ |
| 16 | `tests/test_dhw.py` — endpoint tests | ✅ |
| 17 | `tests/test_application.py` — use case unit tests | ✅ |
| 18 | `tests/test_config.py` — config layering tests | ✅ |
| 19 | `Dockerfile` — update | ✅ |
| 20 | `docker-compose.yml` — update | ✅ |
| 21 | Delete `main.py` and `requirements.txt` | ✅ |
| 22 | Verify: `pytest -v`, no `import logging` in `app/`, Docker build | ✅ |

---

## Target File Structure

```text
atlantis-dhw-api/
├── app/
│   ├── __init__.py
│   ├── config.py                          # Settings — extends BaseServiceSettings
│   │
│   ├── domain/                            # Core — zero framework dependencies
│   │   ├── __init__.py
│   │   ├── models.py                      # DhwStatus, HistoricalPoint dataclasses
│   │   └── exceptions.py                  # DhwDomainError, InfluxUnavailable, etc.
│   │
│   ├── ports/                             # Interfaces (dependency inversion)
│   │   ├── __init__.py
│   │   └── influx_port.py                 # IDhwInfluxPort ABC
│   │
│   ├── application/                       # Use cases (pure functions)
│   │   ├── __init__.py
│   │   └── dhw_service.py                 # get_dhw_status(port) → DhwStatus
│   │
│   └── adapters/
│       ├── influx/                        # InfluxDB adapter
│       │   ├── __init__.py
│       │   └── influx_adapter.py          # InfluxDhwAdapter(IDhwInfluxPort)
│       │
│       └── api/                           # HTTP adapter
│           ├── __init__.py
│           ├── main.py                    # FastAPI app, lifespan, /health, exception handler
│           ├── deps.py                    # DI — provides IDhwInfluxPort
│           ├── schemas.py                 # Pydantic response schemas
│           └── routers/
│               ├── __init__.py
│               └── dhw.py                # GET /dhw
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_dhw.py                        # Endpoint tests (mock adapter)
│   ├── test_application.py                # Use case unit tests (stub port)
│   └── test_config.py                     # Config layering tests
│
├── atlantis.toml                          # Service identity (non-secret config)
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── CHANGELOG.md
```

---

## Step-by-Step Implementation

### Step 2 — `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "atlantis-dhw-api"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100",
    "uvicorn[standard]",
    "influxdb-client",
    "atlantis-core[config] @ git+https://github.com/mclotet/atlantis-core.git#subdirectory=python",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "httpx", "pytest-mock"]
```

Note: `pydantic` and `pydantic-settings` are pulled in transitively via `atlantis-core[config]`.

---

### Step 3 — `atlantis.toml`

Non-secret service identity and config. Committed to the repo.

```toml
# atlantis.toml — DHW API service identity
# Secrets (DHW_INFLUXDB_TOKEN) must be supplied as environment variables.

atl_service_name = "dhw-api"
atl_device_id    = "dhw-api"
atl_group_id     = "basement"
atl_env          = "pro"
atl_log_level    = "WARNING"

dhw_influxdb_url         = "http://influxdb:8086"
dhw_influxdb_org         = "atlantis"
```

---

### Step 4 — `.env.example`

```dotenv
# Required secret — never goes in atlantis.toml
DHW_INFLUXDB_TOKEN=your-token-here

# Optional runtime overrides (defaults live in atlantis.toml / defaults.toml)
# ATL_ENV=itg
# ATL_LOG_LEVEL=DEBUG
```

---

### Step 5 — `app/domain/models.py`

Pure Python dataclasses. Zero framework imports.

```python
from dataclasses import dataclass, field

@dataclass
class HistoricalPoint:
    dt: int      # Unix timestamp (seconds)
    temp: float

@dataclass
class DhwStatus:
    temperature: float | None
    minutes_left: int
    available: bool
    heating_dhw: bool
    dhw_historical: list[HistoricalPoint] = field(default_factory=list)
```

---

### Step 6 — `app/domain/exceptions.py`

```python
class DhwDomainError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)

class InfluxUnavailable(DhwDomainError): ...
class InfluxQueryError(DhwDomainError): ...
```

---

### Step 7 — `app/ports/influx_port.py`

Abstract contract that the use case depends on. The adapter implements it.

```python
from abc import ABC, abstractmethod
from app.domain.models import DhwStatus

class IDhwInfluxPort(ABC):
    @abstractmethod
    async def get_dhw_status(self) -> DhwStatus: ...
```

---

### Step 8 — `app/application/dhw_service.py`

Pure use case function. Depends on the port interface, not any concrete implementation.

```python
from app.ports.influx_port import IDhwInfluxPort
from app.domain.models import DhwStatus

async def get_dhw_status(port: IDhwInfluxPort) -> DhwStatus:
    return await port.get_dhw_status()
```

Note: currently a thin wrapper since all query logic lives in the adapter. The use case layer exists so future business logic (e.g. real `minutes_left` calculation, alerting thresholds) has a natural home without touching the adapter or router.

---

### Step 9 — `app/adapters/influx/influx_adapter.py`

Concrete implementation of `IDhwInfluxPort`. Contains all Flux query logic and InfluxDB details.

```python
import asyncio
from influxdb_client import QueryApi
from app.ports.influx_port import IDhwInfluxPort
from app.domain.models import DhwStatus, HistoricalPoint
from app.domain.exceptions import InfluxQueryError

class InfluxDhwAdapter(IDhwInfluxPort):
    def __init__(self, query_api: QueryApi, settings) -> None:
        self._q = query_api
        self._s = settings

    async def get_dhw_status(self) -> DhwStatus:
        try:
            temp, (op_mode, valve), history = await asyncio.gather(
                asyncio.to_thread(self._query_latest_temp),
                asyncio.to_thread(self._query_heating_state),
                asyncio.to_thread(self._query_historical),
            )
        except Exception as exc:
            raise InfluxQueryError(str(exc)) from exc

        return DhwStatus(
            temperature=temp,
            minutes_left=30,   # placeholder
            available=temp is not None,
            heating_dhw=op_mode and valve,
            dhw_historical=history,
        )

    def _query_latest_temp(self) -> float | None: ...
    def _query_heating_state(self) -> tuple[bool, bool]: ...
    def _query_historical(self) -> list[HistoricalPoint]: ...
```

All three private methods contain the Flux queries currently in `main.py`. Log each with `subsystem="storage"`.

---

### Step 10 — `app/adapters/api/schemas.py`

Pydantic schemas for HTTP responses (separate from domain models, as in atlantis-forge).

```python
from pydantic import BaseModel

class HistoricalPointSchema(BaseModel):
    dt: int
    temp: float

class DhwStatusSchema(BaseModel):
    model_config = {"from_attributes": True}
    temperature: float | None
    minutes_left: int
    available: bool
    heating_dhw: bool
    dhw_historical: list[HistoricalPointSchema]
```

---

### Step 11 — `app/adapters/api/deps.py`

DI wiring. Provides the concrete `IDhwInfluxPort` to routes.

```python
from fastapi import Request
from app.adapters.influx.influx_adapter import InfluxDhwAdapter
from app.ports.influx_port import IDhwInfluxPort

def get_influx_port(request: Request) -> IDhwInfluxPort:
    return InfluxDhwAdapter(
        query_api=request.app.state.query_api,
        settings=request.app.state.settings,
    )
```

---

### Step 12 — `app/adapters/api/routers/dhw.py`

```python
from fastapi import APIRouter, Depends
from app.adapters.api.deps import get_influx_port
from app.adapters.api.schemas import DhwStatusSchema
from app.application import dhw_service
from app.ports.influx_port import IDhwInfluxPort

router = APIRouter()

@router.get("/dhw", response_model=DhwStatusSchema)
async def dhw_status(port: IDhwInfluxPort = Depends(get_influx_port)):
    status = await dhw_service.get_dhw_status(port)
    return DhwStatusSchema.model_validate(status, from_attributes=True)
```

---

### Step 13 — `app/adapters/api/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from atlantis_core import AtlantisLogger
from influxdb_client import InfluxDBClient
from app.config import settings
from app.domain.exceptions import DhwDomainError, InfluxUnavailable, InfluxQueryError
from app.adapters.api.routers import dhw

_STATUS_MAP = {
    InfluxUnavailable: 503,
    InfluxQueryError: 502,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = AtlantisLogger.configure(
        service_name=settings.atl_service_name,
        device_id=settings.atl_device_id,
        group_id=settings.atl_group_id,
    )
    app.state.settings = settings
    app.state.logger = logger
    logger.info("Starting DHW API", extra={"subsystem": "boot"})

    client = InfluxDBClient(
        url=settings.dhw_influxdb_url,
        token=settings.dhw_influxdb_token,
        org=settings.dhw_influxdb_org,
    )
    app.state.influx_client = client
    app.state.query_api = client.query_api()
    logger.info("InfluxDB client ready", extra={"subsystem": "boot"})

    yield

    logger.info("Shutting down DHW API", extra={"subsystem": "shutdown"})
    client.close()

app = FastAPI(title="Atlantis DHW API", lifespan=lifespan)
app.include_router(dhw.router)

@app.exception_handler(DhwDomainError)
async def domain_error_handler(request: Request, exc: DhwDomainError) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "detail": exc.detail},
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

### Step 14 — `app/config.py`

```python
from atlantis_core.config import BaseServiceSettings

class Settings(BaseServiceSettings):
    # ATL_* fields NOT redeclared — values come from atlantis.toml / defaults.toml
    # Per python-services.md §9: do not set Python-level defaults on inherited ATL_* fields

    dhw_influxdb_url: str           # from atlantis.toml
    dhw_influxdb_token: str         # from env var only — never in atlantis.toml
    dhw_influxdb_org: str           # from atlantis.toml
    dhw_influxdb_bucket: str = "altherma"
    dhw_influxdb_measurement: str = "altherma"
    dhw_influxdb_temp_field: str = "DHW_tank_temp_(R5T)"
    dhw_influxdb_op_mode_field: str = "Operation_Mode"
    dhw_influxdb_valve_field: str = "3way_valve(On:DHW_Off:Space)"

settings = Settings()
```

---

### Step 15 — `tests/conftest.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from app.adapters.api.main import app
from app.adapters.api.deps import get_influx_port

@pytest.fixture
def mock_port():
    return AsyncMock()

@pytest.fixture
def client(mock_port):
    app.dependency_overrides[get_influx_port] = lambda: mock_port
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def async_client(client):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
```

---

### Steps 16–18 — Tests

**`test_dhw.py`:**

- `test_dhw_happy_path` — mock port returns full `DhwStatus`; assert HTTP 200 + schema
- `test_dhw_no_temperature` — port returns `DhwStatus(temperature=None, available=False, ...)`; assert `available=false`
- `test_dhw_influx_error` — port raises `InfluxQueryError`; assert HTTP 502
- `test_dhw_influx_unavailable` — port raises `InfluxUnavailable`; assert HTTP 503

**`test_application.py`:**

- `test_get_dhw_status_delegates_to_port` — stub port with known return; assert use case returns it unchanged

**`test_config.py`** (follows `python-services.md` §11):

- `test_config_from_toml` — write `atlantis.toml` to `tmp_path`, `monkeypatch.chdir(tmp_path)`, set `DHW_INFLUXDB_TOKEN`; assert `atl_service_name == "dhw-api"`
- `test_env_overrides_toml` — same setup + `ATL_ENV=itg`; assert env var wins
- `test_missing_token_raises` — no token in env; assert `ValidationError`

---

### Step 19 — `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml atlantis.toml ./
RUN pip install --no-cache-dir .
COPY app/ ./app/
CMD ["uvicorn", "app.adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Step 20 — `docker-compose.yml`

ATL_* values live in `atlantis.toml`. Only secrets need to be passed as env vars.

```yaml
services:
  dhw-api:
    build: .
    container_name: dhw-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DHW_INFLUXDB_TOKEN: ${DHW_INFLUXDB_TOKEN}
```

---

### Step 21 — Delete old files

- `main.py` (root-level)
- `requirements.txt`

---

## Verification (Step 22)

1. `pytest tests/ -v` — all pass, no real InfluxDB connection
2. `grep -r "import logging" app/` — returns nothing (C-04 resolved)
3. Local run: `uvicorn app.adapters.api.main:app --reload` with `DHW_INFLUXDB_TOKEN` set; `GET /health` → `{"status":"ok"}`
4. Log format: `ATL_ENV=dev` in `atlantis.toml` → human-readable; `ATL_ENV=pro` → OTel JSON
5. `docker build -t dhw-api .` succeeds; `docker compose up` responds on port 8000
