from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import AlertSeverity
from app.schemas.alert import AlertResponse
from app.services.alert_service import AlertService

router = APIRouter()


def get_alert_service(db: Annotated[Session, Depends(get_db)]) -> AlertService:
    return AlertService(db)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    service: Annotated[AlertService, Depends(get_alert_service)],
    severity: Annotated[AlertSeverity | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    unresolved_only: Annotated[bool, Query()] = False,
) -> list[AlertResponse]:
    alerts = service.list_alerts(
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        unresolved_only=unresolved_only,
    )
    return [AlertResponse.model_validate(alert, from_attributes=True) for alert in alerts]
