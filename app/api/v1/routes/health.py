from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.health import HealthResponse
from app.services.health_service import HealthService, get_health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    return service.get_health()
