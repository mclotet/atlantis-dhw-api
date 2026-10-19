import asyncio
import logging

from influxdb_client import QueryApi

from app.domain.exceptions import DhwDomainError, InfluxQueryError
from app.domain.models import DhwStatus, HistoricalPoint
from app.ports.influx_port import IDhwInfluxPort

logger = logging.getLogger("atlantis")


class InfluxDhwAdapter(IDhwInfluxPort):
    def __init__(self, query_api: QueryApi, settings) -> None:
        self._q = query_api
        self._s = settings

    async def get_dhw_status(self) -> DhwStatus:
        try:
            temp, heating, history = await asyncio.gather(
                asyncio.to_thread(self._query_latest_temp),
                asyncio.to_thread(self._query_heating_state),
                asyncio.to_thread(self._query_historical),
            )
        except DhwDomainError:
            raise
        except Exception as exc:
            logger.error("InfluxDB query failed: %s", exc, extra={"subsystem": "storage"})
            raise InfluxQueryError(str(exc)) from exc

        return DhwStatus(
            temperature=temp,
            time_left=30,  # placeholder — real calculation tracked separately
            available=temp is not None,
            heating_dhw=heating,
            historical=history,
        )

    def _query_latest_temp(self) -> float | None:
        s = self._s
        query = f"""
from(bucket: "{s.dhw_influxdb_bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "{s.dhw_influxdb_measurement}")
  |> filter(fn: (r) => r._field == "{s.dhw_influxdb_temp_field}")
  |> last()
"""
        logger.debug("Querying latest DHW temperature", extra={"subsystem": "storage"})
        result = self._q.query(org=s.dhw_influxdb_org, query=query)
        if result and result[0].records:
            value = float(result[0].records[0].get_value())
            logger.info("Latest DHW temp %.1f°C", value, extra={"subsystem": "storage"})
            return value
        logger.warning("No DHW temperature data found", extra={"subsystem": "storage"})
        return None

    def _query_heating_state(self) -> bool:
        s = self._s
        # States are published on change and retained, so the last record can be old:
        # look back a day. group() merges the per-device tables so last() is the newest.
        query = f"""
from(bucket: "{s.dhw_influxdb_states_bucket}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "{s.dhw_influxdb_states_measurement}")
  |> filter(fn: (r) => r.sensor_id == "{s.dhw_heating_sensor_id}")
  |> filter(fn: (r) => r._field == "state")
  |> group()
  |> last()
"""
        logger.debug("Querying DHW heating state", extra={"subsystem": "storage"})
        result = self._q.query(org=s.dhw_influxdb_org, query=query)

        for table in result:
            for record in table.records:
                return str(record.get_value()) == s.dhw_heating_state
        return False

    def _query_historical(self) -> list[HistoricalPoint]:
        s = self._s
        query = f"""
from(bucket: "{s.dhw_influxdb_bucket}")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "{s.dhw_influxdb_measurement}")
  |> filter(fn: (r) => r._field == "{s.dhw_influxdb_temp_field}")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> yield(name: "mean")
"""
        logger.debug("Querying DHW historical data", extra={"subsystem": "storage"})
        result = self._q.query(org=s.dhw_influxdb_org, query=query)

        points: list[HistoricalPoint] = []
        for table in result:
            for record in table.records:
                points.append(HistoricalPoint(
                    timestamp=record.get_time().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    temperature=float(record.get_value()),
                ))
        return points
