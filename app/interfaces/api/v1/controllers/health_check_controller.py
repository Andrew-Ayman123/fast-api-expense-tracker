"""Health check controller for verifying API status."""

from fastapi import APIRouter

from app.schemas.health_check_schema import HealthCheckResponse

# versioning is handled in the main file
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health check endpoint")
async def health_check() -> HealthCheckResponse:
    """Perform a health check to verify API status.

    Returns:
        HealthCheckResponse: HealthCheckResponse with status "ok" if the API is healthy.

    """
    return HealthCheckResponse(status="ok")
