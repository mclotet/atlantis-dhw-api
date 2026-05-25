import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from app.adapters.api.deps import get_influx_port
from app.adapters.api.main import app


@pytest.fixture
def mock_port():
    return AsyncMock()


@pytest.fixture
def patched_app(mock_port):
    app.dependency_overrides[get_influx_port] = lambda: mock_port
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(patched_app):
    # lifespan=False: skip startup so tests need no real InfluxDB connection
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
