"""Currency conversion and supported currencies router."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import (
    ConvertRequest,
    ConvertResponse,
    CurrenciesResponse,
    ErrorDetail,
)
from app.services.currency_service import (
    CurrencyService,
    CurrencyServiceError,
    ProviderConnectionError,
    ProviderResponseError,
    ProviderTimeoutError,
    UnsupportedCurrencyError,
    get_currency_service,
)

router = APIRouter(prefix="/api", tags=["Conversion"])


@router.post(
    "/convert",
    response_model=ConvertResponse,
    responses={
        404: {"model": ErrorDetail, "description": "Currency code not supported"},
        422: {"description": "Validation error"},
        502: {"model": ErrorDetail, "description": "Upstream exchange service error"},
        504: {"model": ErrorDetail, "description": "Upstream exchange service timeout"},
    },
    summary="Convert an amount between two currencies",
)
async def convert_currency(
    payload: ConvertRequest,
    service: CurrencyService = Depends(get_currency_service),
) -> ConvertResponse:
    """Execute live or cached currency conversion between two ISO 4217 currency codes."""
    try:
        result = await service.convert(
            amount=payload.amount,
            from_currency=payload.from_currency,
            to_currency=payload.to_currency,
        )
        return ConvertResponse(
            success=True,
            amount=result["amount"],
            from_currency=result["from_currency"],
            to_currency=result["to_currency"],
            exchange_rate=result["exchange_rate"],
            converted_amount=result["converted_amount"],
            rate_last_updated_utc=result.get("rate_last_updated_utc"),
            rate_next_update_utc=result.get("rate_next_update_utc"),
            source=result.get("source", "open.er-api.com"),
        )
    except UnsupportedCurrencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Unsupported Currency", "details": exc.message},
        ) from exc
    except ProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "Provider Timeout", "details": exc.message},
        ) from exc
    except (ProviderConnectionError, ProviderResponseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "Provider Error", "details": exc.message},
        ) from exc
    except CurrencyServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Currency Service Error", "details": exc.message},
        ) from exc


@router.get(
    "/currencies",
    response_model=CurrenciesResponse,
    responses={
        502: {"model": ErrorDetail, "description": "Upstream exchange service error"},
        504: {"model": ErrorDetail, "description": "Upstream exchange service timeout"},
    },
    summary="Get list of supported currency codes",
)
async def list_currencies(
    service: CurrencyService = Depends(get_currency_service),
) -> CurrenciesResponse:
    """Return sorted list of supported currency codes derived from live exchange provider."""
    try:
        result = await service.get_supported_currencies(base_currency="USD")
        return CurrenciesResponse(
            success=True,
            count=result["count"],
            base_currency=result["base_currency"],
            currencies=result["currencies"],
        )
    except ProviderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "Provider Timeout", "details": exc.message},
        ) from exc
    except (ProviderConnectionError, ProviderResponseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "Provider Error", "details": exc.message},
        ) from exc
    except CurrencyServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Currency Service Error", "details": exc.message},
        ) from exc
