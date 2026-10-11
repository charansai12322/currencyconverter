"""Pytest configuration and fixtures for testing."""

from typing import Any, AsyncGenerator, Dict
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from app.main import app
from app.services.currency_service import get_currency_service


MOCK_USD_RATES_DATA: Dict[str, Any] = {
    "result": "success",
    "provider": "https://www.exchangerate-api.com",
    "documentation": "https://www.exchangerate-api.com/docs/free",
    "terms_of_use": "https://www.exchangerate-api.com/terms",
    "time_last_update_unix": 1791676951,
    "time_last_update_utc": "Sun, 11 Oct 2026 00:02:31 +0000",
    "time_next_update_unix": 1791764061,
    "time_next_update_utc": "Mon, 12 Oct 2026 00:14:21 +0000",
    "time_eol_unix": 0,
    "base_code": "USD",
    "rates": {
        "USD": 1.0,
        "AED": 3.6725,
        "EUR": 0.892438,
        "GBP": 0.755923,
        "INR": 96.829695,
        "JPY": 158.287265,
    },
}


@pytest.fixture(autouse=True)
def reset_service_cache() -> None:
    """Ensure in-memory cache is cleared before and after each test."""
    service = get_currency_service()
    service.clear_cache()
    yield
    service.clear_cache()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an asynchronous test client for FastAPI routes."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
