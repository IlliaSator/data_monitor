from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings


class ReportService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_report_path(self, batch_id: str) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        reports_dir = Path(self.settings.reports_dir)
        return reports_dir / f"drift_report_{batch_id}_{timestamp}.html"
