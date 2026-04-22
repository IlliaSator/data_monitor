from datetime import datetime

from pydantic import BaseModel


class PerformanceMetricResponse(BaseModel):
    created_at: datetime
    batch_id: str
    model_version: str
    sample_size: int
    positive_rate: float
    accuracy: float
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    performance_below_threshold: bool
