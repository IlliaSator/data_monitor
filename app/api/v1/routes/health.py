from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService, get_health_service

router = APIRouter()


def get_health_service_dependency(
    db: Annotated[Session, Depends(get_db)],
) -> HealthService:
    return get_health_service(db)


@router.get("/health", response_model=HealthResponse)
def health_check(
    service: Annotated[HealthService, Depends(get_health_service_dependency)],
) -> HealthResponse:
    return service.get_health()
