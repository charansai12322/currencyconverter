"""Comprehensive tests for currency conversion and supported currency listing."""

from unittest.mock import AsyncMock, patch
import pytest
import httpx

from app.services.currency_service import get_currency_service
from tests.conftest import MOCK_USD_RATES_DATA


@pytest.mark.asyncio
async def test_convert_valid_usd_to_inr(async_client: httpx.AsyncClient) -> None:
    """Verify valid USD to INR conversion with mocked upstream provider."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_USD_RATES_DATA

        payload = {"amount": 100.0, "from_currency": "USD", "to_currency": "INR"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["amount"] == 100.0
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "INR"
        assert data["exchange_rate"] == 96.829695
        # 100 * 96.829695 = 9682.9695 -> rounded to 9682.97
        assert data["converted_amount"] == 9682.97
        assert data["rate_last_updated_utc"] == "Sun, 11 Oct 2026 00:02:31 +0000"
        assert data["rate_next_update_utc"] == "Mon, 12 Oct 2026 00:14:21 +0000"
        assert data["source"] == "open.er-api.com"
        mock_fetch.assert_awaited_once_with("USD")


@pytest.mark.asyncio
async def test_convert_currency_normalization(async_client: httpx.AsyncClient) -> None:
    """Verify that lowercase codes with whitespace are normalized to uppercase."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_USD_RATES_DATA

        payload = {"amount": 50, "from_currency": " usd ", "to_currency": " eur "}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "EUR"
        assert data["exchange_rate"] == 0.892438
        assert data["converted_amount"] == 44.62


@pytest.mark.asyncio
async def test_convert_same_currency_shortcut(async_client: httpx.AsyncClient) -> None:
    """Verify same-currency conversion returns rate 1.0 without calling upstream provider."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        payload = {"amount": 250.75, "from_currency": "USD", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 250.75
        assert data["exchange_rate"] == 1.0
        assert data["converted_amount"] == 250.75
        assert data["source"] == "internal"
        # Verify provider was NOT called
        mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_convert_zero_amount(async_client: httpx.AsyncClient) -> None:
    """Verify zero amount returns zero converted amount."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_USD_RATES_DATA

        payload = {"amount": 0.0, "from_currency": "USD", "to_currency": "EUR"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 0.0
        assert data["converted_amount"] == 0.0


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validation_negative_amount(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of negative amounts."""
    payload = {"amount": -10.0, "from_currency": "USD", "to_currency": "INR"}
    response = await async_client.post("/api/convert", json=payload)
    assert response.status_code == 422
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_validation_boolean_amount(async_client: httpx.AsyncClient) -> None:
    """Verify explicit rejection of boolean values as amount."""
    payload = {"amount": True, "from_currency": "USD", "to_currency": "INR"}
    response = await async_client.post("/api/convert", json=payload)
    assert response.status_code == 422
    assert "boolean" in response.json()["details"].lower()


@pytest.mark.asyncio
async def test_validation_excessive_amount(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of amounts exceeding reasonable maximum limit."""
    payload = {"amount": 1e15, "from_currency": "USD", "to_currency": "INR"}
    response = await async_client.post("/api/convert", json=payload)
    assert response.status_code == 422
    assert "exceeds" in response.json()["details"].lower()


@pytest.mark.asyncio
async def test_validation_malformed_currency_code(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of malformed or non-3-letter currency codes."""
    # 2-letter code
    res1 = await async_client.post("/api/convert", json={"amount": 10, "from_currency": "US", "to_currency": "INR"})
    assert res1.status_code == 422

    # 4-letter code
    res2 = await async_client.post("/api/convert", json={"amount": 10, "from_currency": "USD", "to_currency": "INRR"})
    assert res2.status_code == 422

    # Numeric code
    res3 = await async_client.post("/api/convert", json={"amount": 10, "from_currency": "123", "to_currency": "INR"})
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_validation_extra_fields_forbidden(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of unauthorized extra fields."""
    payload = {"amount": 100, "from_currency": "USD", "to_currency": "INR", "extra_field": "disallowed"}
    response = await async_client.post("/api/convert", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Provider Failure Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_unsupported_target_currency(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 404 when target currency is not in provider rates."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_USD_RATES_DATA

        payload = {"amount": 100, "from_currency": "USD", "to_currency": "XYZ"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "unsupported" in data["details"].lower()


@pytest.mark.asyncio
async def test_provider_timeout_handling(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 504 Gateway Timeout when upstream provider times out."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.ReadTimeout("Read timed out")
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "INR"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 504
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Provider Timeout"
    finally:
        service._client = original_client


@pytest.mark.asyncio
async def test_provider_connection_error_handling(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 502 Bad Gateway when upstream provider cannot be reached."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "INR"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Provider Error"
    finally:
        service._client = original_client


@pytest.mark.asyncio
async def test_provider_unsupported_source_currency(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 404 when upstream provider returns unsupported-code error."""
    mock_response = httpx.Response(
        status_code=200,
        json={"result": "error", "error-type": "unsupported-code"},
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/ZZZ"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "ZZZ", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "unsupported" in data["details"].lower()
    finally:
        service._client = original_client


# ---------------------------------------------------------------------------
# Supported Currencies Endpoint Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_supported_currencies(async_client: httpx.AsyncClient) -> None:
    """Verify GET /api/currencies returns sorted list of available currencies."""
    service = get_currency_service()

    with patch.object(service, "fetch_rates_for_base", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_USD_RATES_DATA

        response = await async_client.get("/api/currencies")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 6
        assert data["base_currency"] == "USD"
        assert data["currencies"] == ["AED", "EUR", "GBP", "INR", "JPY", "USD"]


# ---------------------------------------------------------------------------
# In-Memory Caching Verification Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_in_memory_caching_behavior() -> None:
    """Verify that successive queries for same base currency use cache and avoid redundant requests."""
    mock_response = httpx.Response(
        status_code=200,
        json=MOCK_USD_RATES_DATA,
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/USD"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    service._client = mock_client

    # First call - cache miss, should call upstream
    res1 = await service.convert(100, "USD", "INR")
    assert res1["converted_amount"] == 9682.97
    assert mock_client.get.call_count == 1

    # Second call - cache hit, should NOT call upstream again
    res2 = await service.convert(200, "USD", "EUR")
    assert res2["converted_amount"] == 178.49
    assert mock_client.get.call_count == 1


# ---------------------------------------------------------------------------
# Additional Validation & Provider Edge Case Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validation_nan_and_infinity(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of NaN and Infinity via raw payload and Pydantic validator."""
    from pydantic import ValidationError
    from app.schemas import ConvertRequest

    # Test raw non-compliant string payload rejected by API
    headers = {"Content-Type": "application/json"}
    res_nan = await async_client.post(
        "/api/convert",
        content='{"amount": NaN, "from_currency": "USD", "to_currency": "INR"}',
        headers=headers,
    )
    assert res_nan.status_code == 422

    res_inf = await async_client.post(
        "/api/convert",
        content='{"amount": Infinity, "from_currency": "USD", "to_currency": "INR"}',
        headers=headers,
    )
    assert res_inf.status_code == 422

    # Verify Pydantic schema rejection directly
    with pytest.raises(ValidationError) as exc1:
        ConvertRequest(amount=float("nan"), from_currency="USD", to_currency="INR")
    assert "finite" in str(exc1.value)

    with pytest.raises(ValidationError) as exc2:
        ConvertRequest(amount=float("inf"), from_currency="USD", to_currency="INR")
    assert "finite" in str(exc2.value)



@pytest.mark.asyncio
async def test_validation_missing_fields(async_client: httpx.AsyncClient) -> None:
    """Verify rejection when required fields are missing."""
    res1 = await async_client.post("/api/convert", json={"from_currency": "USD", "to_currency": "INR"})
    assert res1.status_code == 422

    res2 = await async_client.post("/api/convert", json={"amount": 100, "to_currency": "INR"})
    assert res2.status_code == 422

    res3 = await async_client.post("/api/convert", json={"amount": 100, "from_currency": "USD"})
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_validation_string_non_numeric_amount(async_client: httpx.AsyncClient) -> None:
    """Verify rejection of non-numeric string amount."""
    payload = {"amount": "not-a-number", "from_currency": "USD", "to_currency": "INR"}
    response = await async_client.post("/api/convert", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_provider_http_500_error(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 502 when upstream provider returns HTTP 500 error."""
    mock_response = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/EUR"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)
        assert response.status_code == 502
        assert response.json()["error"] == "Provider Error"
    finally:
        service._client = original_client


@pytest.mark.asyncio
async def test_provider_invalid_json(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 502 when upstream provider returns invalid non-JSON."""
    mock_response = httpx.Response(
        status_code=200,
        text="<html>Service Unavailable</html>",
        headers={"content-type": "text/html"},
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/EUR"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)
        assert response.status_code == 502
    finally:
        service._client = original_client


@pytest.mark.asyncio
async def test_provider_missing_rates(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 502 when upstream provider returns JSON without rates."""
    mock_response = httpx.Response(
        status_code=200,
        json={"result": "success", "base_code": "EUR", "rates": {}},
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/EUR"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)
        assert response.status_code == 502
    finally:
        service._client = original_client


@pytest.mark.asyncio
async def test_provider_unexpected_base_currency(async_client: httpx.AsyncClient) -> None:
    """Verify HTTP 502 when upstream returns a base currency that differs from requested."""
    mock_response = httpx.Response(
        status_code=200,
        json={"result": "success", "base_code": "GBP", "rates": {"USD": 1.3}},
        request=httpx.Request("GET", "https://open.er-api.com/v6/latest/EUR"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False

    service = get_currency_service()
    original_client = service._client
    service._client = mock_client

    try:
        payload = {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}
        response = await async_client.post("/api/convert", json=payload)
        assert response.status_code == 502
    finally:
        service._client = original_client

