from fastapi import Request

from app.adapters.influx.influx_adapter import InfluxDhwAdapter
from app.ports.influx_port import IDhwInfluxPort


def get_influx_port(request: Request) -> IDhwInfluxPort:
    return InfluxDhwAdapter(
        query_api=request.app.state.query_api,
        settings=request.app.state.settings,
    )
