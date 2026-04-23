from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.model_service import FEATURE_COLUMNS


def main() -> None:
    dataset_path = Path("data/public_credit_scoring_sample.csv")
    if not dataset_path.exists():
        raise FileNotFoundError(
            "Public credit sample was not found. Run scripts/prepare_public_dataset.py first."
        )

    frame = pd.read_csv(dataset_path)
    features = frame[FEATURE_COLUMNS]
    target = frame["actual_default"].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.25,
        random_state=42,
        stratify=target,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = probabilities >= 0.5
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "f1_score": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
    }

    artifact = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "threshold": 0.5,
        "training_data": str(dataset_path),
        "metrics": metrics,
    }

    output_path = Path("models/credit_scoring_model.joblib")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)

    print(f"Saved model artifact to {output_path}")
    print(f"Holdout metrics: {metrics}")


if __name__ == "__main__":
    main()
