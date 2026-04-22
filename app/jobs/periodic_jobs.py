from __future__ import annotations

import logging

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.batch import Batch
from app.models.drift_report import DriftReport
from app.services.retrain_service import RetrainService

logger = logging.getLogger(__name__)


def refresh_monitoring_snapshot() -> None:
    with SessionLocal() as db:
        batch_count = db.scalar(select(func.count(Batch.id))) or 0
        drift_report_count = db.scalar(select(func.count(DriftReport.id))) or 0
        open_alert_count = (
            db.scalar(select(func.count(Alert.id)).where(Alert.resolved.is_(False))) or 0
        )
        logger.info(
            "Monitoring snapshot refreshed: batches=%s reports=%s open_alerts=%s",
            batch_count,
            drift_report_count,
            open_alert_count,
        )


def reconcile_retrain_flags() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        latest_drift = db.scalar(select(DriftReport).order_by(DriftReport.created_at.desc()))
        if latest_drift is None:
            return
        if latest_drift.global_drift_score >= settings.alert_threshold:
            RetrainService(db, settings).mark_retrain_required(
                "Scheduler detected sustained drift above alert threshold."
            )
            db.commit()
            logger.info("Retrain flag reconciled for model=%s", latest_drift.model_version)
