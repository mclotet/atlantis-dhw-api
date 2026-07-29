# Changelog

All notable changes to this project will be documented in this file.
Format: Keep a Changelog (https://keepachangelog.com) — `[Unreleased]` / `[version] - YYYY-MM-DD`
Categories: Added | Changed | Deprecated | Removed | Fixed | Security

## [Unreleased]

### Changed
- Re-pin `libs/atlantis-core` submodule from `929aa84` to `32c4425` (CTRL-033), catching up 81
  commits behind `origin/main`. Covers CORE-048 (Python MQTT topic/payload builders aligned
  byte-for-byte with C++/MQTT-standard: flat `build_state` JSON, camelCase `build_log` OTel
  envelope, `%.6g` telemetry number formatting), CORE-049 (new `atlantis_core.health` check
  toolkit), CORE-050–059 (NTP drift/stratum/timestamp fixes), and CORE-065–074 (HTTPS transport,
  Infisical secret sync, WiFi PSK rotation, WiFi NVS host-side provisioning tool) through the
  firmware/native side of the library. None of these touch the surface this service actually
  uses — `AtlantisLogger.configure(service_name, device_id, group_id)` (no `mqtt_client`, so
  `MqttLogHandler`/`mqtt_payload.build_log` is never constructed) and `BaseServiceSettings`,
  neither of which changed in this range — so the bump was verified in one incremental pass
  (checkpoints at `2de8c14`, `d0f4296`, `bdc19e2`, then tip) with no source changes required.
  Full scoped `pytest` suite (9 tests) passes at every checkpoint and at the tip.

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
