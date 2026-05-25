from atlantis_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    # ATL_* fields intentionally NOT redeclared here.
    # Values come from atlantis.toml (deployment) → defaults.toml (framework).
    # Per python-services.md §9: do not set Python-level defaults on inherited ATL_* fields.

    # Required — must be in atlantis.toml or env vars (no sensible universal default)
    dhw_influxdb_url: str
    dhw_influxdb_org: str

    # Secret — must be supplied as env var; never in atlantis.toml
    dhw_influxdb_token: str

    # Service-specific optional fields with sensible Python defaults
    dhw_influxdb_bucket: str = "altherma"
    dhw_influxdb_measurement: str = "altherma"
    dhw_influxdb_temp_field: str = "DHW_tank_temp_(R5T)"
    dhw_influxdb_op_mode_field: str = "Operation_Mode"
    dhw_influxdb_valve_field: str = "3way_valve(On:DHW_Off:Space)"


def get_settings() -> "Settings":
    return Settings()
