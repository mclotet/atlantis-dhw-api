# Changelog

All notable changes to this project will be documented in this file.
Format: Keep a Changelog (https://keepachangelog.com) — `[Unreleased]` / `[version] - YYYY-MM-DD`
Categories: Added | Changed | Deprecated | Removed | Fixed | Security

## [Unreleased]

### Added
- Woodpecker CI pipeline (`.woodpecker/{itg,pro}.yml`): submodule fetch, scoped pytest suite, Docker build

## [0.1.0] - 2026-03-12

### Added
- FastAPI REST service for domestic hot water (DHW) queries against InfluxDB
- InfluxDB client integration for reading DHW telemetry
- Environment variable configuration (`DHW_INFLUXDB_*`) for InfluxDB connection
- Docker image and standalone docker-compose.yml for deployment via atlantis-controller
- `.env.example` with all required environment variables documented

### Notes
- Uses standard Python `logging` instead of AtlantisLogger — tracked as C-04 in audit-report-2026-05-02.md. Planned fix in a future release.
- InfluxDB client initialised once at startup with no reconnection logic — tracked as W-14. Planned fix in a future release.
