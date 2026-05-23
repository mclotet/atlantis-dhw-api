from app.domain.models import DhwStatus
from app.ports.influx_port import IDhwInfluxPort


async def get_dhw_status(port: IDhwInfluxPort) -> DhwStatus:
    """Retrieve current DHW status via the provided port.

    Thin wrapper today; exists so future business logic (real time_left
    calculation, alerting thresholds) has a natural home without touching
    the adapter or router.
    """
    return await port.get_dhw_status()
