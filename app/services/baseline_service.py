from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.baseline import Baseline


class BaselineService:
    feature_columns = [
        "age",
        "annual_income",
        "debt_to_income",
        "credit_utilization",
        "num_open_accounts",
        "delinquency_count",
        "loan_amount",
        "employment_years",
    ]

    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def get_or_create_active_baseline(self) -> Baseline:
        statement = (
            select(Baseline)
            .where(Baseline.is_active.is_(True))
            .order_by(Baseline.created_at.desc())
        )
        baseline = self.db.scalar(statement)
        if baseline is not None:
            return baseline

        baseline_path = Path(self.settings.baseline_path)
        if not baseline_path.exists():
            raise FileNotFoundError(
                f"Baseline file was not found at '{baseline_path}'. "
                "Create it before ingesting data."
            )

        baseline_frame = pd.read_csv(baseline_path)
        version = baseline_path.stem

        baseline = Baseline(
            version=version,
            name="Credit scoring baseline",
            description="Initial reference distribution loaded from CSV artifact.",
            source_path=str(baseline_path),
            artifact_path=str(baseline_path),
            row_count=len(baseline_frame),
            is_active=True,
        )
        self.db.add(baseline)
        self.db.flush()
        return baseline

    def load_baseline_frame(self, baseline: Baseline) -> pd.DataFrame:
        baseline_frame = pd.read_csv(baseline.artifact_path)
        missing_columns = [
            column for column in self.feature_columns if column not in baseline_frame.columns
        ]
        if missing_columns:
            joined_columns = ", ".join(missing_columns)
            raise ValueError(f"Baseline file is missing required columns: {joined_columns}")
        return baseline_frame[self.feature_columns]
