from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.baseline import Baseline
from app.schemas.baseline import BaselineResponse


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

    def reinitialize_baseline(
        self,
        *,
        source_csv_path: str | None,
        dataset_path: str | None,
        sample_size: int | None,
        name: str,
        description: str | None,
    ) -> BaselineResponse:
        source_frame = self._load_source_frame(
            source_csv_path=source_csv_path,
            dataset_path=dataset_path,
            sample_size=sample_size,
        )
        baseline_frame = source_frame[self.feature_columns].copy()

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        artifact_dir = Path("data/baselines")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        version = f"baseline_{timestamp}"
        artifact_path = artifact_dir / f"{version}.csv"
        baseline_frame.to_csv(artifact_path, index=False)

        active_baselines = self.db.scalars(
            select(Baseline).where(Baseline.is_active.is_(True))
        ).all()
        for baseline in active_baselines:
            baseline.is_active = False

        baseline = Baseline(
            version=version,
            name=name,
            description=description or "Baseline snapshot created via API reinitialization.",
            source_path=source_csv_path or dataset_path or self.settings.baseline_path,
            artifact_path=str(artifact_path),
            row_count=len(baseline_frame),
            is_active=True,
        )
        self.db.add(baseline)
        self.db.commit()
        self.db.refresh(baseline)

        return BaselineResponse.model_validate(baseline, from_attributes=True)

    def load_baseline_frame(self, baseline: Baseline) -> pd.DataFrame:
        baseline_frame = pd.read_csv(baseline.artifact_path)
        missing_columns = [
            column for column in self.feature_columns if column not in baseline_frame.columns
        ]
        if missing_columns:
            joined_columns = ", ".join(missing_columns)
            raise ValueError(f"Baseline file is missing required columns: {joined_columns}")
        return baseline_frame[self.feature_columns]

    def _load_source_frame(
        self,
        *,
        source_csv_path: str | None,
        dataset_path: str | None,
        sample_size: int | None,
    ) -> pd.DataFrame:
        selected_path = source_csv_path or dataset_path
        if selected_path is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A source path is required to initialize baseline.",
            )

        source_path = Path(selected_path)
        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source file '{source_path}' was not found.",
            )

        dataframe = pd.read_csv(source_path)
        if dataset_path is not None and sample_size is not None:
            dataframe = dataframe.head(sample_size)

        missing_columns = [
            column for column in self.feature_columns if column not in dataframe.columns
        ]
        if missing_columns:
            joined_columns = ", ".join(missing_columns)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Source data is missing required columns: {joined_columns}",
            )
        return dataframe
