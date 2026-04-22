from app.models.alert import Alert
from app.models.batch import Batch
from app.models.drift_report import DriftReport, FeatureDriftMetric
from app.models.enums import AlertSeverity
from app.services.alert_service import AlertService


def test_alert_service_creates_feature_and_global_alerts(db_session):
    batch = Batch(
        external_id="batch-alert-1",
        model_version="credit_scoring_v1",
        baseline_version="baseline_v1",
        size=2,
        schema_version="v1",
    )
    db_session.add(batch)
    db_session.flush()

    drift_report = DriftReport(
        batch_id=batch.id,
        baseline_version="baseline_v1",
        model_version="credit_scoring_v1",
        global_drift_score=0.92,
        drift_detected=True,
        alert_triggered=True,
        feature_count=2,
    )
    db_session.add(drift_report)
    db_session.flush()

    feature_metrics = [
        FeatureDriftMetric(
            drift_report_id=drift_report.id,
            feature_name="credit_utilization",
            drift_score=0.83,
            threshold=0.4,
            is_drifted=True,
        ),
        FeatureDriftMetric(
            drift_report_id=drift_report.id,
            feature_name="age",
            drift_score=0.12,
            threshold=0.4,
            is_drifted=False,
        ),
    ]

    service = AlertService(db_session)
    alerts = service.create_alerts_for_report(drift_report, feature_metrics, alert_threshold=0.7)
    db_session.commit()

    persisted_alerts = db_session.query(Alert).all()
    assert len(alerts) == 2
    assert len(persisted_alerts) == 2
    assert any(alert.feature_name is None for alert in persisted_alerts)
    assert any(alert.severity == AlertSeverity.high for alert in persisted_alerts)
