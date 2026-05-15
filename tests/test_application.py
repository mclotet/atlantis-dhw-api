from unittest.mock import AsyncMock

from app.application import dhw_service
from app.domain.models import DhwStatus, HistoricalPoint


async def test_get_dhw_status_delegates_to_port():
    expected = DhwStatus(
        temperature=48.5,
        minutes_left=30,
        available=True,
        heating_dhw=False,
        dhw_historical=[HistoricalPoint(dt=1715520060, temp=48.1)],
    )
    port = AsyncMock()
    port.get_dhw_status.return_value = expected

    result = await dhw_service.get_dhw_status(port)

    port.get_dhw_status.assert_awaited_once()
    assert result is expected
