from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.metrics import MetricsHistoryResponse
from app.services.metrics_service import MetricsService

router = APIRouter()


def get_metrics_service(db: Annotated[Session, Depends(get_db)]) -> MetricsService:
    return MetricsService(db)


@router.get("/metrics/history", response_model=MetricsHistoryResponse)
def get_metrics_history(
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    model_version: Annotated[str | None, Query()] = None,
    baseline_version: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> MetricsHistoryResponse:
    return service.get_history(
        model_version=model_version,
        baseline_version=baseline_version,
        date_from=date_from,
        date_to=date_to,
    )
