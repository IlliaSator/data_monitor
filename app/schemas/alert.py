from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertStatus


class AlertResponse(BaseModel):
    id: int
    feature_name: str | None
    drift_score: float
    threshold: float
    created_at: datetime
    severity: AlertSeverity
    status: AlertStatus
    resolved: bool
    message: str | None


class AlertStatusUpdateRequest(BaseModel):
    status: AlertStatus

    model_config = ConfigDict(extra="forbid")
