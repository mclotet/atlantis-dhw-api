from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.adapters.influx.influx_adapter import InfluxDhwAdapter
from app.config import Settings


def _settings():
    return Settings.model_construct(
        dhw_influxdb_org="atlantis",
        dhw_influxdb_states_bucket="atlantis-states",
        dhw_influxdb_states_measurement="altherma_states",
        dhw_heating_sensor_id="heatpump",
        dhw_heating_state="DHW",
    )


def _result(*values):
    records = [SimpleNamespace(get_value=lambda v=v: v) for v in values]
    return [SimpleNamespace(records=records)] if records else []


@pytest.mark.parametrize(
    "values, expected",
    [(("DHW",), True), (("HEATING",), False), (("STANDBY",), False), ((), False)],
)
def test_heating_state(values, expected):
    q = MagicMock()
    q.query.return_value = _result(*values)
    adapter = InfluxDhwAdapter(q, _settings())

    assert adapter._query_heating_state() is expected


def test_heating_state_queries_altherma_states():
    q = MagicMock()
    q.query.return_value = []
    InfluxDhwAdapter(q, _settings())._query_heating_state()

    flux = q.query.call_args.kwargs["query"]
    assert 'from(bucket: "atlantis-states")' in flux
    assert 'r._measurement == "altherma_states"' in flux
    assert 'r.sensor_id == "heatpump"' in flux
    assert 'r._field == "state"' in flux
    assert "Operation_Mode" not in flux
