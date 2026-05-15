import logging

from fastapi import APIRouter, Depends

from app.adapters.api.deps import get_influx_port
from app.adapters.api.schemas import DhwStatusSchema
from app.application import dhw_service
from app.ports.influx_port import IDhwInfluxPort

router = APIRouter()
logger = logging.getLogger("atlantis")


@router.get("/dhw", response_model=DhwStatusSchema)
async def dhw_status(port: IDhwInfluxPort = Depends(get_influx_port)):
    logger.debug("Handling GET /dhw", extra={"subsystem": "api"})
    status = await dhw_service.get_dhw_status(port)
    return DhwStatusSchema.model_validate(status, from_attributes=True)
