from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.batch import Batch
from app.models.model_version import ModelVersion
from app.models.prediction_log import PredictionLog
from app.monitoring.quality_checks import run_quality_checks
from app.schemas.ingest import IngestRequest, IngestResponse, PredictionLogResponse
from app.services.drift_service import DriftService
from app.services.performance_service import PerformanceService


class IngestionService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def ingest_batch(self, payload: IngestRequest) -> IngestResponse:
        batch_id = payload.batch_id or f"batch-{uuid4().hex[:12]}"
        dataframe = pd.DataFrame(
            [record.model_dump(exclude={"actual_default"}) for record in payload.records]
        )
        quality_result = run_quality_checks(dataframe)

        if self._batch_exists(batch_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Batch with id '{batch_id}' already exists.",
            )

        if not quality_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Batch failed data quality checks.",
                    "warnings": quality_result.warnings,
                    "quality_summary": quality_result.summary,
                },
            )

        try:
            self._ensure_model_version_exists()

            batch = Batch(
                external_id=batch_id,
                model_version=self.settings.model_version,
                baseline_version=None,
                size=len(payload.records),
                request_metadata=payload.metadata,
                quality_summary=quality_result.summary,
                warnings=quality_result.warnings,
                ingest_completed_at=datetime.now(UTC),
            )
            self.db.add(batch)
            self.db.flush()

            prediction_logs = []
            response_predictions: list[PredictionLogResponse] = []
            prediction_values: list[float] = []
            actual_labels: list[bool] = []
            for record in payload.records:
                record_payload = record.model_dump()
                actual_label = record_payload.pop("actual_default", None)
                prediction_value = self._score_record(record_payload)
                prediction_label = "high_risk" if prediction_value >= 0.5 else "low_risk"
                prediction_logs.append(
                    PredictionLog(
                        batch_id=batch.id,
                        customer_id=record.customer_id,
                        prediction=prediction_value,
                        prediction_label=prediction_label,
                        actual_label=actual_label,
                        model_version=self.settings.model_version,
                        features=record_payload,
                    )
                )
                response_predictions.append(
                    PredictionLogResponse(
                        customer_id=record.customer_id,
                        prediction=prediction_value,
                        prediction_label=prediction_label,
                    )
                )
                prediction_values.append(prediction_value)
                if actual_label is not None:
                    actual_labels.append(actual_label)

            self.db.add_all(prediction_logs)
            drift_report = DriftService(self.db, self.settings).analyze_batch(
                batch=batch,
                current_records=[record.model_dump() for record in payload.records],
            )
            performance_tracked = len(actual_labels) == len(payload.records)
            if performance_tracked:
                PerformanceService(self.db).create_batch_metrics(
                    batch=batch,
                    predictions=prediction_values,
                    actual_labels=actual_labels,
                    model_version=self.settings.model_version,
                )
            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist batch ingestion results.",
            ) from exc

        return IngestResponse(
            batch_id=batch.external_id,
            size=batch.size,
            drift_status="drift_detected" if drift_report.drift_detected else "stable",
            warnings=quality_result.warnings,
            timestamp=batch.ingest_completed_at or datetime.now(UTC),
            model_version=batch.model_version,
            baseline_version=batch.baseline_version,
            quality_summary=quality_result.summary,
            predictions=response_predictions,
            performance_tracked=performance_tracked,
        )

    def _batch_exists(self, batch_id: str) -> bool:
        statement = select(Batch.id).where(Batch.external_id == batch_id)
        return self.db.scalar(statement) is not None

    def _ensure_model_version_exists(self) -> None:
        statement = select(ModelVersion).where(ModelVersion.version == self.settings.model_version)
        model_version = self.db.scalar(statement)
        if model_version is None:
            self.db.add(
                ModelVersion(
                    version=self.settings.model_version,
                    name="Credit scoring monitor model",
                    description="Baseline demo model for monitoring workflows.",
                    stage="production",
                    is_active=True,
                )
            )
            self.db.flush()

    def _score_record(self, record: dict[str, float | int | str]) -> float:
        raw_score = (
            0.18 * float(record["debt_to_income"])
            + 0.22 * float(record["credit_utilization"])
            + 0.12 * float(record["delinquency_count"]) / 10
            + 0.14 * float(record["loan_amount"]) / 50000
            - 0.10 * float(record["annual_income"]) / 150000
            - 0.08 * float(record["employment_years"]) / 10
            - 0.06 * float(record["num_open_accounts"]) / 12
            - 0.04 * float(record["age"]) / 100
        )
        normalized = min(max(raw_score + 0.45, 0.0), 1.0)
        return round(normalized, 4)


def get_ingestion_service(db: Session) -> IngestionService:
    return IngestionService(db=db, settings=get_settings())
