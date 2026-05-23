from unittest.mock import AsyncMock

from app.application import dhw_service
from app.domain.models import DhwStatus, HistoricalPoint


async def test_get_dhw_status_delegates_to_port():
    expected = DhwStatus(
        temperature=48.5,
        time_left=30,
        available=True,
        heating_dhw=False,
        historical=[HistoricalPoint(timestamp="2024-05-12T16:01:00Z", temperature=48.1)],
    )
    port = AsyncMock()
    port.get_dhw_status.return_value = expected

    result = await dhw_service.get_dhw_status(port)

    port.get_dhw_status.assert_awaited_once()
    assert result is expected
