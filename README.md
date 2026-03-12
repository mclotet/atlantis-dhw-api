# atlantis-dhw-api

REST API that exposes Domestic Hot Water (DHW) status by querying an InfluxDB instance. Returns current tank temperature, heating state, availability, and 30-minute historical temperatures.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/dhw` | Returns current DHW status and historical temperatures |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

## Standalone usage

Requires an external InfluxDB instance reachable at `DHW_INFLUXDB_URL` with the appropriate bucket, measurement, and field already populated.

```bash
cp .env.example .env
# Edit .env: set DHW_INFLUXDB_URL, DHW_INFLUXDB_TOKEN, DHW_INFLUXDB_ORG,
#            DHW_INFLUXDB_BUCKET, DHW_INFLUXDB_MEASUREMENT, DHW_INFLUXDB_TEMP_FIELD
docker compose up
```

The API will be available at `http://localhost:8000`.

## Environment variables

| Variable | Description | Example |
|---|---|---|
| `DHW_INFLUXDB_URL` | URL of the InfluxDB instance | `http://localhost:8086` |
| `DHW_INFLUXDB_TOKEN` | InfluxDB API token with read access to the bucket | `my-token` |
| `DHW_INFLUXDB_ORG` | InfluxDB organisation name | `my-org` |
| `DHW_INFLUXDB_BUCKET` | InfluxDB bucket containing DHW data | `altherma` |
| `DHW_INFLUXDB_MEASUREMENT` | InfluxDB measurement name | `altherma` |
| `DHW_INFLUXDB_TEMP_FIELD` | InfluxDB field name for DHW tank temperature | `DHW_tank_temp_(R5T)` |

## Deployment via atlantis-controller

When deployed as part of [atlantis-controller](https://github.com/your-org/atlantis-controller), this service is built and managed by the controller's `docker-compose.yml` and accessed via `http://dhw.atlantis.home`. The controller's `.env` is the authoritative configuration source — this repo's `.env.example` and `docker-compose.yml` are for standalone use only.
