from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RetrainTriggerRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)

    model_config = ConfigDict(extra="forbid")


class RetrainTriggerResponse(BaseModel):
    model_version: str
    retrain_required: bool
    reason: str
    triggered_at: datetime


class RetrainingEventResponse(BaseModel):
    id: int
    model_version: str
    reason: str
    triggered_by: str
    drift_score: float | None
    resolved: bool
    created_at: datetime
