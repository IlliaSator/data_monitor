from __future__ import annotations

from dataclasses import asdict

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.batch import Batch
from app.models.drift_report import DriftReport, FeatureDriftMetric
from app.monitoring.drift_calculator import (
    FeatureDriftResult,
    calculate_feature_drift,
    calculate_global_drift_score,
)
from app.monitoring.evidently_runner import EvidentlyRunner
from app.services.baseline_service import BaselineService
from app.services.report_service import ReportService


class DriftService:
    feature_columns = BaselineService.feature_columns

    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.baseline_service = BaselineService(db=db, settings=settings)
        self.report_service = ReportService(settings=settings)
        self.evidently_runner = EvidentlyRunner()

    def analyze_batch(self, batch: Batch, current_records: list[dict]) -> DriftReport:
        baseline = self.baseline_service.get_or_create_active_baseline()
        reference_frame = self.baseline_service.load_baseline_frame(baseline)
        current_frame = pd.DataFrame(current_records)[self.feature_columns]

        feature_results = calculate_feature_drift(
            reference_data=reference_frame,
            current_data=current_frame,
            threshold=self.settings.feature_drift_threshold,
        )
        global_score = calculate_global_drift_score(feature_results)
        report_path = self.report_service.build_report_path(batch.external_id)
        evidently_snapshot = self.evidently_runner.build_report(
            reference_data=reference_frame,
            current_data=current_frame,
            output_path=report_path,
        )

        drift_report = DriftReport(
            batch_id=batch.id,
            baseline_version=baseline.version,
            model_version=batch.model_version,
            global_drift_score=global_score,
            drift_detected=global_score >= self.settings.drift_threshold,
            alert_triggered=global_score >= self.settings.alert_threshold,
            feature_count=len(feature_results),
            report_path=str(report_path),
            report_metadata={
                "evidently_snapshot_keys": sorted(evidently_snapshot.keys()),
                "evidently_metric_count": len(evidently_snapshot.get("metrics", [])),
                "feature_results": [asdict(result) for result in feature_results],
            },
        )
        self.db.add(drift_report)
        self.db.flush()

        self._persist_feature_metrics(drift_report.id, feature_results)

        batch.baseline_version = baseline.version
        self.db.flush()
        return drift_report

    def _persist_feature_metrics(
        self,
        drift_report_id: int,
        feature_results: list[FeatureDriftResult],
    ) -> None:
        metrics = [
            FeatureDriftMetric(
                drift_report_id=drift_report_id,
                feature_name=result.feature_name,
                drift_score=result.drift_score,
                threshold=result.threshold,
                is_drifted=result.is_drifted,
                metric_details=result.metric_details,
            )
            for result in feature_results
        ]
        self.db.add_all(metrics)
