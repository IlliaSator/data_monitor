from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.drift_report import DriftReport, FeatureDriftMetric
from app.models.enums import AlertSeverity, AlertStatus


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_alerts_for_report(
        self,
        drift_report: DriftReport,
        feature_metrics: list[FeatureDriftMetric],
        alert_threshold: float,
    ) -> list[Alert]:
        alerts: list[Alert] = []

        if drift_report.global_drift_score >= alert_threshold:
            alerts.append(
                Alert(
                    drift_report_id=drift_report.id,
                    feature_name=None,
                    drift_score=drift_report.global_drift_score,
                    threshold=alert_threshold,
                    severity=self._resolve_severity(
                        drift_report.global_drift_score,
                        alert_threshold,
                    ),
                    status=AlertStatus.open,
                    resolved=False,
                    message="Global drift score exceeded alert threshold.",
                )
            )

        for feature_metric in feature_metrics:
            if feature_metric.drift_score < feature_metric.threshold:
                continue
            alerts.append(
                Alert(
                    drift_report_id=drift_report.id,
                    feature_name=feature_metric.feature_name,
                    drift_score=feature_metric.drift_score,
                    threshold=feature_metric.threshold,
                    severity=self._resolve_severity(
                        feature_metric.drift_score,
                        feature_metric.threshold,
                    ),
                    status=AlertStatus.open,
                    resolved=False,
                    message=f"Feature drift threshold exceeded for {feature_metric.feature_name}.",
                )
            )

        self.db.add_all(alerts)
        return alerts

    def list_alerts(
        self,
        severity: AlertSeverity | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        unresolved_only: bool = False,
    ) -> list[Alert]:
        statement: Select[tuple[Alert]] = select(Alert).order_by(Alert.created_at.desc())

        if severity is not None:
            statement = statement.where(Alert.severity == severity)
        if date_from is not None:
            statement = statement.where(Alert.created_at >= date_from)
        if date_to is not None:
            statement = statement.where(Alert.created_at <= date_to)
        if unresolved_only:
            statement = statement.where(Alert.status != AlertStatus.resolved)

        return list(self.db.scalars(statement).all())

    def _resolve_severity(self, drift_score: float, threshold: float) -> AlertSeverity:
        ratio = drift_score / max(threshold, 1e-6)
        if ratio >= 1.5:
            return AlertSeverity.high
        if ratio >= 1.15:
            return AlertSeverity.medium
        return AlertSeverity.low
