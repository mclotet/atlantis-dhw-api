from contextlib import asynccontextmanager

from atlantis_core import AtlantisLogger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from influxdb_client import InfluxDBClient

from app.adapters.api.routers import dhw
from app.config import get_settings
from app.domain.exceptions import DhwDomainError, InfluxQueryError, InfluxUnavailable

_STATUS_MAP = {
    InfluxUnavailable: 503,
    InfluxQueryError: 502,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger = AtlantisLogger.configure(
        service_name=settings.atl_service_name,
        device_id=settings.atl_device_id,
        group_id=settings.atl_group_id,
    )
    app.state.settings = settings
    app.state.logger = logger
    logger.info("Starting DHW API", extra={"subsystem": "boot"})

    client = InfluxDBClient(
        url=settings.dhw_influxdb_url,
        token=settings.dhw_influxdb_token,
        org=settings.dhw_influxdb_org,
    )
    app.state.influx_client = client
    app.state.query_api = client.query_api()
    logger.info("InfluxDB client ready", extra={"subsystem": "boot"})

    yield

    logger.info("Shutting down DHW API", extra={"subsystem": "shutdown"})
    client.close()


app = FastAPI(title="Atlantis DHW API", lifespan=lifespan)
app.include_router(dhw.router)


@app.exception_handler(DhwDomainError)
async def domain_error_handler(request: Request, exc: DhwDomainError) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "detail": exc.detail},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
