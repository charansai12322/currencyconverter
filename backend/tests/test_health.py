"""Tests for health check, root, and CORS configuration."""

import pytest
import httpx


@pytest.mark.asyncio
async def test_health_endpoint_success(async_client: httpx.AsyncClient) -> None:
    """Verify that GET /health returns HTTP 200 and healthy status."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: httpx.AsyncClient) -> None:
    """Verify that GET / returns API metadata and links."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Currency Converter API"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_cors_headers_allowed_origin(async_client: httpx.AsyncClient) -> None:
    """Verify that allowed origin receives CORS access headers."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    response = await async_client.options("/api/convert", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_cors_headers_disallowed_origin(async_client: httpx.AsyncClient) -> None:
    """Verify that disallowed origin does not receive access headers."""
    headers = {
        "Origin": "http://malicious-site.example.com",
        "Access-Control-Request-Method": "POST",
    }
    response = await async_client.options("/api/convert", headers=headers)
    assert response.headers.get("access-control-allow-origin") != "http://malicious-site.example.com"


def test_settings_gemini_api_key_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that GEMINI_API_KEY defaults to None when unset and loads properly when set."""
    from app.config import Settings

    # Case 1: When environment variable is set
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-key")
    settings_with_key = Settings(_env_file=None)
    assert settings_with_key.GEMINI_API_KEY == "test-mock-key"

    # Case 2: When environment variable is unset
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    settings_without_key = Settings(_env_file=None)
    assert settings_without_key.GEMINI_API_KEY is None

