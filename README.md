# atlantis-dhw-api

REST API that exposes Domestic Hot Water (DHW) status by querying an InfluxDB instance. Returns current tank temperature, heating state, availability, and 30-minute historical temperatures.

## Architecture

```text
atlantis-altherma (ESP32)
    → MQTT → Telegraf → InfluxDB
                                  ↑
                            atlantis-dhw-api (FastAPI)
                                  ↓
                            REST consumers (HA, Grafana, etc.)
```

A stateless, read-only FastAPI service. It queries InfluxDB directly on every request — there is no caching layer and no persistent state of its own. Built on `atlantis-core` (git submodule) for `BaseServiceSettings` configuration and `AtlantisLogger` structured logging.

## Key files

| File | Responsibility |
| --- | --- |
| `app/config.py` | Service settings — InfluxDB connection and field mapping, extends `BaseServiceSettings` |
| `app/domain/models.py` | Domain data classes — `DhwStatus`, `HistoricalPoint` |
| `app/domain/exceptions.py` | Domain error types (`InfluxUnavailable`, `InfluxQueryError`) mapped to HTTP status codes |
| `app/ports/influx_port.py` | `IDhwInfluxPort` — abstract port the application layer depends on |
| `app/application/dhw_service.py` | Use-case orchestration — retrieves DHW status via the injected port |
| `app/adapters/influx/influx_adapter.py` | InfluxDB adapter implementing `IDhwInfluxPort`; runs the Flux queries |
| `app/adapters/api/main.py` | FastAPI app factory, lifespan (settings/logger/InfluxDB client startup), exception handler |
| `app/adapters/api/deps.py` | FastAPI dependency wiring — builds `InfluxDhwAdapter` from app state |
| `app/adapters/api/routers/dhw.py` | `/dhw` route handler |
| `app/adapters/api/schemas.py` | Pydantic response schemas |

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/dhw` | Returns current DHW status and historical temperatures |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

### `GET /dhw`

Returns the current DHW tank status and the last 30 minutes of historical temperatures.

**Response — `200 OK`:**

```json
{
  "temperature": 52.3,
  "time_left": 30,
  "available": true,
  "heating_dhw": true,
  "historical": [
    {
      "timestamp": "2026-05-24T10:15:00Z",
      "temperature": 52.1
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `temperature` | `float \| null` | Current DHW tank temperature (°C). `null` if no reading in the last 5 min. |
| `time_left` | `int` | Estimated time until DHW is ready (minutes). Placeholder — always 30 for now. |
| `available` | `bool` | `true` when a current temperature reading exists. |
| `heating_dhw` | `bool` | `true` when the latest `heatpump` state of the Altherma (last 24 h, `altherma_states` in the states bucket) is `DHW`, i.e. the 3-way valve is in the DHW position. `false` for any other mode or when no state is found. |
| `historical[].timestamp` | `string` | ISO 8601 UTC timestamp of the 1-minute aggregate bucket. |
| `historical[].temperature` | `float` | Mean DHW tank temperature over the 1-minute bucket (°C). |

**Error responses:**

| Status | Error | Cause |
|---|---|---|
| `502` | `InfluxQueryError` | Any InfluxDB query or connection failure (error, timeout, connection refused) |
| `503` | `InfluxUnavailable` | Reserved — defined but not currently raised |

Error body: `{"error": "<ExceptionName>", "detail": "<message>"}`.

### `GET /health`

Returns `{"status": "ok"}` with HTTP 200 when the service is running.

## Standalone usage

Requires an external InfluxDB instance reachable at `DHW_INFLUXDB_URL` with the appropriate bucket, measurement, and field already populated.

```bash
git clone https://github.com/mclotet/atlantis-dhw-api.git
cd atlantis-dhw-api
git submodule update --init --recursive
cp .env.example .env
# Edit .env: set DHW_INFLUXDB_TOKEN and ATL_DHW_EDGE_NODE_ID; override DHW_INFLUXDB_URL
#            (the atlantis.toml default points at the compose hostname `influxdb`)
docker compose up
```

The API will be available at `http://localhost:8000`.

## Environment variables

These are the variables the service itself reads at runtime. Required ones have no default; the rest default from `atlantis.toml` or `app/config.py`.

| Variable | Description | Default |
| --- | --- | --- |
| `DHW_INFLUXDB_URL` | URL of the InfluxDB instance (required; override for standalone runs) | `http://influxdb:8086` (`atlantis.toml`) |
| `DHW_INFLUXDB_TOKEN` | InfluxDB API token with read access to the telemetry and states buckets (required, secret) | — |
| `DHW_INFLUXDB_ORG` | InfluxDB organisation name | `atlantis` (`atlantis.toml`) |
| `DHW_INFLUXDB_BUCKET` | Bucket containing DHW temperatures | `atlantis-telemetry` |
| `DHW_INFLUXDB_MEASUREMENT` | Measurement of the DHW temperature | `altherma_water_temps` |
| `DHW_INFLUXDB_TEMP_FIELD` | Field of the DHW tank temperature | `dhw` |
| `DHW_INFLUXDB_STATES_BUCKET` | Bucket containing Altherma states | `atlantis-states` |
| `DHW_INFLUXDB_STATES_MEASUREMENT` | Measurement of the Altherma states | `altherma_states` |
| `DHW_HEATING_SENSOR_ID` | `sensor_id` tag whose state decides `heating_dhw` | `heatpump` |
| `DHW_HEATING_STATE` | State value that means "heating DHW" | `DHW` |
| `ATL_*` | Identity and logging (`ATL_ENV`, `ATL_LOG_LEVEL`, ...), inherited from `atlantis-core` `BaseServiceSettings` | `atlantis.toml` |
| `ATL_DHW_EDGE_NODE_ID` | Compose-only: becomes `ATLANTIS_EDGE_NODE_ID` inside the container | `infra` |
| `LOG_FORMAT` | `json` (default) or `human` | `json` |

## Deployment via atlantis-controller

When deployed as part of [atlantis-controller](https://github.com/mclotet/atlantis-controller), this service is built and managed by the controller's `docker-compose.yml` and accessed via `http://dhw.atlantis.home`.

### How variables are set in atlantis-controller

The controller's `docker-compose.yml` has no `env_file` for this service: only the variables listed in its `environment:` block reach the container.

| Controller variable | Passed to container as |
| --- | --- |
| `DHW_INFLUXDB_URL` | `DHW_INFLUXDB_URL` |
| `DHW_INFLUXDB_BUCKET` | `DHW_INFLUXDB_BUCKET` |
| `DHW_INFLUXDB_MEASUREMENT` | `DHW_INFLUXDB_MEASUREMENT` |
| `DHW_INFLUXDB_TEMP_FIELD` | `DHW_INFLUXDB_TEMP_FIELD` |
| `ATL_DHW_EDGE_NODE_ID` | `ATLANTIS_EDGE_NODE_ID` |
| `ATL_DHW_ENV` | `ATL_ENV` |

`DHW_INFLUXDB_ORG` is not forwarded: the container uses the `atlantis.toml` default. The states settings (`DHW_INFLUXDB_STATES_*`, `DHW_HEATING_*`) are not forwarded either and use their defaults.

> **Note:** The `DHW_INFLUXDB_TOKEN` is created by the `influxdb2-provisioner` sidecar, but stored in Infisical (`/docker`, key `DHW_INFLUXDB_TOKEN`). It reaches the container as the Docker secret `dhw-influxdb-token`; it is not set in the controller's `.env.static`. The token needs read access to both `atlantis-telemetry` and `atlantis-states`.

Edit the `DHW_*` section in the controller's `.env.static` — not in this repo.
