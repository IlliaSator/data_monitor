from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.core.config import Settings

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "age",
    "annual_income",
    "debt_to_income",
    "credit_utilization",
    "num_open_accounts",
    "delinquency_count",
    "loan_amount",
    "employment_years",
]


class ModelPredictor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._artifact: Any | None = None
        self._artifact_path: Path | None = None

    def predict_default_probability(self, record: dict[str, float | int | str]) -> float:
        artifact = self._load_artifact()
        if artifact is None:
            return self._fallback_score(record)

        model = artifact.get("model") if isinstance(artifact, dict) else artifact
        feature_columns = (
            artifact.get("feature_columns", FEATURE_COLUMNS)
            if isinstance(artifact, dict)
            else FEATURE_COLUMNS
        )
        frame = pd.DataFrame([{column: record[column] for column in feature_columns}])
        probability = float(model.predict_proba(frame)[0][1])
        return round(min(max(probability, 0.0), 1.0), 4)

    def _load_artifact(self) -> Any | None:
        if not self.settings.model_path:
            return None

        artifact_path = Path(self.settings.model_path)
        if self._artifact is not None and self._artifact_path == artifact_path:
            return self._artifact

        if not artifact_path.exists():
            logger.warning(
                "Model artifact not found at %s; using rule-based fallback.", artifact_path
            )
            return None

        self._artifact = joblib.load(artifact_path)
        self._artifact_path = artifact_path
        logger.info("Loaded model artifact from %s", artifact_path)
        return self._artifact

    def _fallback_score(self, record: dict[str, float | int | str]) -> float:
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
