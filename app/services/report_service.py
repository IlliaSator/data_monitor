from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.drift_report import DriftReport


class ReportService:
    def __init__(self, settings: Settings, db: Session | None = None) -> None:
        self.settings = settings
        self.db = db

    def build_report_path(self, batch_id: str) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        reports_dir = Path(self.settings.reports_dir)
        return reports_dir / f"drift_report_{batch_id}_{timestamp}.html"

    def get_latest_report(self) -> DriftReport | None:
        if self.db is None:
            return None

        statement = select(DriftReport).order_by(DriftReport.created_at.desc())
        latest_report = self.db.scalar(statement)
        if latest_report is None or latest_report.report_path is None:
            return None

        report_path = Path(latest_report.report_path)
        if not report_path.exists():
            return None
        return latest_report


def get_report_service(db: Session) -> ReportService:
    from app.core.config import get_settings

    return ReportService(settings=get_settings(), db=db)
