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
    dhw_influxdb_bucket: str = "atlantis-telemetry"
    dhw_influxdb_measurement: str = "altherma_water_temps"
    dhw_influxdb_temp_field: str = "dhw"

    # Heating state: altherma publishes the heat pump mode as a retained scalar state
    # (atlantis/<group>/state/altherma/<device>/heatpump/status), which Telegraf writes to
    # altherma_states (field "state", tag sensor_id) in the states bucket. The 3-way valve
    # has no sensor of its own: the valve bit in reg 0x60 sets the mode to "DHW".
    dhw_influxdb_states_bucket: str = "atlantis-states"
    dhw_influxdb_states_measurement: str = "altherma_states"
    dhw_heating_sensor_id: str = "heatpump"
    dhw_heating_state: str = "DHW"


def get_settings() -> "Settings":
    return Settings()
