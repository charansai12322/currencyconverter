"""Currency conversion service providing rate retrieval, caching, and arithmetic."""

import copy
import time
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings


class CurrencyServiceError(Exception):
    """Base exception for currency service errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class UnsupportedCurrencyError(CurrencyServiceError):
    """Raised when source or target currency is unsupported by the provider."""


class ProviderConnectionError(CurrencyServiceError):
    """Raised when upstream provider cannot be reached."""


class ProviderTimeoutError(CurrencyServiceError):
    """Raised when upstream provider times out."""


class ProviderResponseError(CurrencyServiceError):
    """Raised when upstream provider returns an invalid or error response."""


class CurrencyService:
    """Service for querying exchange rates and executing currency conversions."""

    BASE_URL = "https://open.er-api.com/v6/latest"

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize currency service with optional injected async client."""
        self._client = client
        self._cache: Dict[str, Dict[str, Any]] = {}

    def clear_cache(self) -> None:
        """Clear in-memory exchange rate cache (used for test isolation)."""
        self._cache.clear()

    async def _get_client(self) -> httpx.AsyncClient:
        """Return injected or ephemeral client with configured timeout."""
        if self._client is not None and not self._client.is_closed:
            return self._client
        settings = get_settings()
        timeout = httpx.Timeout(settings.API_TIMEOUT_SECONDS, connect=5.0)
        return httpx.AsyncClient(timeout=timeout)

    async def fetch_rates_for_base(self, base_currency: str) -> Dict[str, Any]:
        """Fetch exchange rate data for a given base currency with in-memory caching."""
        base_currency = base_currency.strip().upper()
        now = time.time()

        # Check in-memory cache
        if base_currency in self._cache:
            entry = self._cache[base_currency]
            if now < entry["expires_at"]:
                return copy.deepcopy(entry["data"])
            else:
                del self._cache[base_currency]

        settings = get_settings()
        url = f"{self.BASE_URL}/{base_currency}"
        should_close_client = self._client is None or self._client.is_closed

        try:
            client = await self._get_client()
            try:
                response = await client.get(url)
            finally:
                if should_close_client:
                    await client.aclose()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Exchange rate service request timed out.",
                details=str(exc),
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderConnectionError(
                "Could not establish connection to the exchange rate service.",
                details=str(exc),
            ) from exc

        if response.status_code >= 400:
            raise ProviderResponseError(
                f"Exchange rate service returned HTTP error status {response.status_code}.",
                details=response.text[:200],
            )

        try:
            data = response.json()
        except Exception as exc:
            raise ProviderResponseError(
                "Exchange rate service returned invalid non-JSON payload.",
                details=str(exc),
            ) from exc

        if not isinstance(data, dict):
            raise ProviderResponseError("Exchange rate service response must be a JSON object.")

        result_status = data.get("result")
        if result_status != "success":
            error_type = data.get("error-type", "Unknown error")
            if error_type == "unsupported-code":
                raise UnsupportedCurrencyError(
                    f"Source currency '{base_currency}' is unsupported by the exchange rate service.",
                    details=error_type,
                )
            raise ProviderResponseError(
                f"Exchange rate service reported failure for base currency '{base_currency}'.",
                details=error_type,
            )

        returned_base = data.get("base_code")
        if returned_base != base_currency:
            raise ProviderResponseError(
                f"Upstream provider returned base currency '{returned_base}', expected '{base_currency}'."
            )

        rates = data.get("rates")
        if not isinstance(rates, dict) or not rates:
            raise ProviderResponseError("Exchange rate service returned empty or malformed rates dictionary.")

        # Determine cache expiry
        next_update_unix = data.get("time_next_update_unix")
        if isinstance(next_update_unix, (int, float)) and next_update_unix > now:
            ttl = min(float(next_update_unix - now), float(settings.CACHE_TTL_SECONDS))
        else:
            ttl = float(settings.CACHE_TTL_SECONDS)

        # Store in cache
        self._cache[base_currency] = {
            "expires_at": now + ttl,
            "data": data,
        }

        return copy.deepcopy(data)

    async def convert(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Convert amount between two currencies according to verified business rules."""
        from_currency = from_currency.strip().upper()
        to_currency = to_currency.strip().upper()

        # Handle zero amount shortcut
        if amount == 0.0:
            if from_currency == to_currency:
                return {
                    "amount": 0.0,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "exchange_rate": 1.0,
                    "converted_amount": 0.0,
                    "rate_last_updated_utc": None,
                    "rate_next_update_utc": None,
                    "source": "internal",
                }

        # Handle same-currency conversion shortcut without upstream request
        if from_currency == to_currency:
            return {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": 1.0,
                "converted_amount": round(amount, 2),
                "rate_last_updated_utc": None,
                "rate_next_update_utc": None,
                "source": "internal",
            }

        # Retrieve live or cached rates
        data = await self.fetch_rates_for_base(from_currency)
        rates = data.get("rates", {})

        if to_currency not in rates:
            raise UnsupportedCurrencyError(
                f"Target currency '{to_currency}' is unsupported by the exchange rate service."
            )

        raw_rate = rates[to_currency]
        try:
            exchange_rate = float(raw_rate)
            if exchange_rate <= 0:
                raise ValueError()
        except (TypeError, ValueError) as exc:
            raise ProviderResponseError(
                f"Invalid or non-positive exchange rate received for '{to_currency}'."
            ) from exc

        converted_amount = amount * exchange_rate

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": exchange_rate,
            "converted_amount": round(converted_amount, 2),
            "rate_last_updated_utc": data.get("time_last_update_utc"),
            "rate_next_update_utc": data.get("time_next_update_utc"),
            "source": "open.er-api.com",
        }

    async def get_supported_currencies(self, base_currency: str = "USD") -> Dict[str, Any]:
        """Fetch list of supported currency codes derived from an authoritative provider response."""
        data = await self.fetch_rates_for_base(base_currency)
        rates = data.get("rates", {})
        currency_codes = sorted(list(rates.keys()))
        return {
            "base_currency": base_currency,
            "count": len(currency_codes),
            "currencies": currency_codes,
        }


# Singleton service instance for FastAPI dependency injection
_service_instance: Optional[CurrencyService] = None


def get_currency_service() -> CurrencyService:
    """Return singleton instance of CurrencyService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CurrencyService()
    return _service_instance
