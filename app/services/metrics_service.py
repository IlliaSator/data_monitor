from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.batch import Batch
from app.models.drift_report import DriftReport, FeatureDriftMetric
from app.schemas.metrics import (
    FeatureDriftHistoryPoint,
    GlobalDriftPoint,
    MetricsHistoryResponse,
)
from app.services.performance_service import PerformanceService


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_history(
        self,
        model_version: str | None = None,
        baseline_version: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> MetricsHistoryResponse:
        drift_statement: Select[tuple[DriftReport]] = (
            select(DriftReport)
            .join(Batch, Batch.id == DriftReport.batch_id)
            .options(joinedload(DriftReport.batch))
            .order_by(DriftReport.created_at.desc())
        )

        if model_version is not None:
            drift_statement = drift_statement.where(DriftReport.model_version == model_version)
        if baseline_version is not None:
            drift_statement = drift_statement.where(
                DriftReport.baseline_version == baseline_version
            )
        if date_from is not None:
            drift_statement = drift_statement.where(DriftReport.created_at >= date_from)
        if date_to is not None:
            drift_statement = drift_statement.where(DriftReport.created_at <= date_to)

        drift_reports = list(self.db.scalars(drift_statement).unique().all())
        report_ids = [report.id for report in drift_reports]

        feature_metrics: list[FeatureDriftMetric] = []
        if report_ids:
            feature_statement: Select[tuple[FeatureDriftMetric]] = (
                select(FeatureDriftMetric)
                .join(DriftReport, DriftReport.id == FeatureDriftMetric.drift_report_id)
                .join(Batch, Batch.id == DriftReport.batch_id)
                .options(joinedload(FeatureDriftMetric.drift_report).joinedload(DriftReport.batch))
                .where(FeatureDriftMetric.drift_report_id.in_(report_ids))
                .order_by(FeatureDriftMetric.created_at.desc())
            )
            feature_metrics = list(self.db.scalars(feature_statement).unique().all())

        return MetricsHistoryResponse(
            global_metrics=[
                GlobalDriftPoint(
                    created_at=report.created_at,
                    batch_id=report.batch.external_id,
                    model_version=report.model_version,
                    baseline_version=report.baseline_version,
                    global_drift_score=report.global_drift_score,
                    drift_detected=report.drift_detected,
                    alert_triggered=report.alert_triggered,
                )
                for report in drift_reports
            ],
            feature_metrics=[
                FeatureDriftHistoryPoint(
                    created_at=metric.created_at,
                    feature_name=metric.feature_name,
                    drift_score=metric.drift_score,
                    threshold=metric.threshold,
                    is_drifted=metric.is_drifted,
                    model_version=metric.drift_report.model_version,
                    baseline_version=metric.drift_report.baseline_version,
                    batch_id=metric.drift_report.batch.external_id,
                )
                for metric in feature_metrics
            ],
            performance_metrics=PerformanceService(self.db).list_history(),
        )
