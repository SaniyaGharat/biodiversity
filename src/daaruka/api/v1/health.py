"""Health check endpoints and status schemas."""

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field
from daaruka.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Schema for service health status response."""

    status: str = Field(default="healthy", description="Overall health state")
    service: str = Field(default="daaruka-backend", description="Service identifier")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    environment: str = Field(default="production", description="Environment mode")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the health status and metadata of the Daaruka backend service.",
)
async def get_health() -> HealthResponse:
    """Check backend operational health status."""
    return HealthResponse(
        status="healthy",
        service="daaruka-backend",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment="development" if settings.DEBUG else "production",
    )
