"""Health check router."""

from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service health status check")
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return process health status without invoking external network dependencies."""
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
    )
