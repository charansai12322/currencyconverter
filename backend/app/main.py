"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

from app.config import get_settings
from app.routers.convert import router as convert_router
from app.routers.health import router as health_router
from app.services.currency_service import get_currency_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle for shared resources."""
    settings = get_settings()
    # Initialize shared AsyncClient with connection timeouts
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.API_TIMEOUT_SECONDS, connect=5.0)
    )
    app.state.http_client = client
    # Inject client into singleton currency service
    service = get_currency_service()
    service._client = client

    yield

    # Cleanup upon shutdown
    await client.aclose()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Currency Converter API",
        description="High-performance, production-ready currency conversion service backed by ExchangeRate-API.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    allowed_origins = settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standardize validation error responses
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error_messages = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            error_messages.append(f"{loc}: {msg}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation Error",
                "details": "; ".join(error_messages),
            },
        )

    # Standardize HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, dict):
            error_title = exc.detail.get("error", "Error")
            details = exc.detail.get("details", "")
        else:
            error_title = "Error"
            details = str(exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": error_title,
                "details": details,
            },
        )

    # Mount routers
    app.include_router(health_router)
    app.include_router(convert_router)

    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root status descriptor."""
        return {
            "name": "Currency Converter API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_url": "/health",
        }

    return app


app = create_application()
