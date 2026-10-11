"""Pydantic schemas for request and response validation."""

import math
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


CURRENCY_CODE_REGEX = re.compile(r"^[A-Z]{3}$")
MAX_ALLOWED_AMOUNT = 1_000_000_000_000.0  # 1 Trillion


class ConvertRequest(BaseModel):
    """Currency conversion request payload."""

    model_config = ConfigDict(extra="forbid")

    amount: float = Field(
        ...,
        description="Amount of money to convert. Must be non-negative and finite.",
        examples=[100.0],
    )
    from_currency: str = Field(
        ...,
        description="Three-letter ISO 4217 source currency code.",
        examples=["USD"],
    )
    to_currency: str = Field(
        ...,
        description="Three-letter ISO 4217 target currency code.",
        examples=["INR"],
    )

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: object) -> float:
        """Validate numeric value, rejecting bools, NaN, Infinity, negative, and excessive amounts."""
        if isinstance(v, bool):
            raise ValueError("Amount cannot be a boolean value.")
        try:
            num = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError("Amount must be a valid numeric value.")

        if math.isnan(num) or math.isinf(num):
            raise ValueError("Amount must be a finite number.")
        if num < 0:
            raise ValueError("Amount cannot be negative.")
        if num > MAX_ALLOWED_AMOUNT:
            raise ValueError(f"Amount exceeds maximum allowed limit of {MAX_ALLOWED_AMOUNT:,.0f}.")
        return num

    @field_validator("from_currency", "to_currency", mode="before")
    @classmethod
    def normalize_currency_code(cls, v: object) -> str:
        """Strip whitespace, uppercase, and validate 3-letter alphabetic ISO code."""
        if not isinstance(v, str):
            raise ValueError("Currency code must be a string.")
        normalized = v.strip().upper()
        if not CURRENCY_CODE_REGEX.fullmatch(normalized):
            raise ValueError(f"Currency code '{v}' must be a valid 3-letter uppercase alphabetic code.")
        return normalized


class ConvertResponse(BaseModel):
    """Currency conversion response payload."""

    success: bool = True
    amount: float
    from_currency: str
    to_currency: str
    exchange_rate: float
    converted_amount: float
    rate_last_updated_utc: Optional[str] = None
    rate_next_update_utc: Optional[str] = None
    source: str = "open.er-api.com"


class CurrenciesResponse(BaseModel):
    """Supported currencies response payload."""

    success: bool = True
    count: int
    base_currency: str
    currencies: List[str]


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = "healthy"
    environment: str
    version: str = "1.0.0"


class ErrorDetail(BaseModel):
    """Standardized error response payload."""

    success: bool = False
    error: str
    details: Optional[str] = None
