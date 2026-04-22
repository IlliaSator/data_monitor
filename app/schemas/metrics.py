from datetime import datetime

from pydantic import BaseModel

from app.schemas.performance import PerformanceMetricResponse


class GlobalDriftPoint(BaseModel):
    created_at: datetime
    batch_id: str
    model_version: str
    baseline_version: str
    global_drift_score: float
    drift_detected: bool
    alert_triggered: bool


class FeatureDriftHistoryPoint(BaseModel):
    created_at: datetime
    feature_name: str
    drift_score: float
    threshold: float
    is_drifted: bool
    model_version: str
    baseline_version: str
    batch_id: str


class MetricsHistoryResponse(BaseModel):
    global_metrics: list[GlobalDriftPoint]
    feature_metrics: list[FeatureDriftHistoryPoint]
    performance_metrics: list[PerformanceMetricResponse]
