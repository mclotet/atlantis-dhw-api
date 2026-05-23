import pytest

from app.domain.exceptions import InfluxQueryError, InfluxUnavailable
from app.domain.models import DhwStatus, HistoricalPoint


async def test_dhw_happy_path(client, mock_port):
    mock_port.get_dhw_status.return_value = DhwStatus(
        temperature=52.3,
        time_left=30,
        available=True,
        heating_dhw=True,
        historical=[HistoricalPoint(timestamp="2024-05-12T16:00:00Z", temperature=51.8)],
    )

    response = await client.get("/dhw")

    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == pytest.approx(52.3)
    assert data["available"] is True
    assert data["heating_dhw"] is True
    assert data["time_left"] == 30
    assert len(data["historical"]) == 1
    assert data["historical"][0]["timestamp"] == "2024-05-12T16:00:00Z"
    assert data["historical"][0]["temperature"] == pytest.approx(51.8)


async def test_dhw_no_temperature(client, mock_port):
    mock_port.get_dhw_status.return_value = DhwStatus(
        temperature=None,
        time_left=30,
        available=False,
        heating_dhw=False,
        historical=[],
    )

    response = await client.get("/dhw")

    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] is None
    assert data["available"] is False


async def test_dhw_influx_query_error(client, mock_port):
    mock_port.get_dhw_status.side_effect = InfluxQueryError("connection refused")

    response = await client.get("/dhw")

    assert response.status_code == 502
    assert response.json()["error"] == "InfluxQueryError"


async def test_dhw_influx_unavailable(client, mock_port):
    mock_port.get_dhw_status.side_effect = InfluxUnavailable("client not initialised")

    response = await client.get("/dhw")

    assert response.status_code == 503
    assert response.json()["error"] == "InfluxUnavailable"


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
