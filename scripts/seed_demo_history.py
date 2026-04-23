from __future__ import annotations

import argparse
import json
import math
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

FEATURE_COLUMNS = [
    "customer_id",
    "age",
    "annual_income",
    "debt_to_income",
    "credit_utilization",
    "num_open_accounts",
    "delinquency_count",
    "loan_amount",
    "employment_years",
    "actual_default",
]


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"POST {url} failed with {exc.code}: {detail}") from exc


def _build_batch(frame: pd.DataFrame, batch_id: str, scenario: str) -> dict[str, Any]:
    records = frame[FEATURE_COLUMNS].copy()
    records["customer_id"] = records["customer_id"].astype(str) + f"-{scenario}"

    if scenario == "mild-income-shift":
        records["annual_income"] = (records["annual_income"] * 0.78).round(2)
        records["debt_to_income"] = (records["debt_to_income"] * 1.18).clip(upper=0.95).round(4)
    elif scenario == "utilization-pressure":
        records["credit_utilization"] = (
            (records["credit_utilization"] * 1.35).clip(upper=0.98).round(4)
        )
        records["delinquency_count"] = (records["delinquency_count"] + 1).clip(upper=20)
    elif scenario == "high-risk-applicants":
        records["annual_income"] = (records["annual_income"] * 0.62).round(2)
        records["debt_to_income"] = (records["debt_to_income"] * 1.45).clip(upper=0.95).round(4)
        records["credit_utilization"] = (
            (records["credit_utilization"] * 1.5).clip(upper=0.98).round(4)
        )
        records["loan_amount"] = (records["loan_amount"] * 1.35).round(2)
        records["delinquency_count"] = (records["delinquency_count"] + 2).clip(upper=20)

    return {
        "batch_id": batch_id,
        "metadata": {
            "source": "seed_demo_history.py",
            "scenario": scenario,
            "created_at": datetime.now(UTC).isoformat(),
        },
        "records": [
            {key: _json_safe(value) for key, value in record.items()}
            for record in records.to_dict(orient="records")
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo monitoring history through the API.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", default="data/public_credit_scoring_sample.csv")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--prefix", default=datetime.now(UTC).strftime("demo-%Y%m%d%H%M%S"))
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"{dataset_path} was not found. Run scripts/prepare_public_dataset.py first."
        )

    frame = pd.read_csv(dataset_path)
    scenarios = [
        "reference-like",
        "mild-income-shift",
        "utilization-pressure",
        "high-risk-applicants",
    ]

    for index, scenario in enumerate(scenarios):
        start = 260 + index * args.batch_size
        sample = frame.iloc[start : start + args.batch_size].copy()
        batch_id = f"{args.prefix}-{index + 1:02d}-{scenario}"
        payload = _build_batch(sample, batch_id=batch_id, scenario=scenario)
        response = _post_json(f"{args.api_url.rstrip('/')}/ingest", payload)
        print(
            f"{batch_id}: status={response['drift_status']} "
            f"size={response['size']} performance={response['performance_tracked']}"
        )


if __name__ == "__main__":
    main()
