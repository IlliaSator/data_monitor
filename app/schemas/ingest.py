from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreditApplicationRecord(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=18, le=100)
    annual_income: float = Field(gt=0)
    debt_to_income: float = Field(ge=0, le=1)
    credit_utilization: float = Field(ge=0, le=1)
    num_open_accounts: int = Field(ge=0, le=50)
    delinquency_count: int = Field(ge=0, le=20)
    loan_amount: float = Field(gt=0)
    employment_years: float = Field(ge=0, le=50)

    model_config = ConfigDict(extra="forbid", strict=True)


class IngestRequest(BaseModel):
    batch_id: str | None = Field(default=None, max_length=64)
    records: list[CreditApplicationRecord]
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("records")
    @classmethod
    def validate_records_not_empty(
        cls, value: list[CreditApplicationRecord]
    ) -> list[CreditApplicationRecord]:
        if not value:
            raise ValueError("records must not be empty")
        return value


class PredictionLogResponse(BaseModel):
    customer_id: str
    prediction: float
    prediction_label: str


class IngestResponse(BaseModel):
    batch_id: str
    size: int
    drift_status: str
    warnings: list[str]
    timestamp: datetime
    model_version: str
    baseline_version: str | None
    quality_summary: dict[str, Any]
    predictions: list[PredictionLogResponse]
