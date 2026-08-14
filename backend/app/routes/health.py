"""
AI News Analyzer — Health Check Router
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current health status of the API service.",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: status 'ok' and service name.
    """
    return HealthResponse(
        status="ok",
        service="AI News Analyzer API",
    )
