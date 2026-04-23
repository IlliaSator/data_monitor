from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.datasets import fetch_openml

CHECKING_SCORE = {
    "<0": 0.85,
    "0<=X<200": 0.55,
    ">=200": 0.25,
    "no checking": 0.45,
}

SAVINGS_SCORE = {
    "<100": 0.85,
    "100<=X<500": 0.65,
    "500<=X<1000": 0.45,
    ">=1000": 0.25,
    "no known savings": 0.55,
}

EMPLOYMENT_YEARS = {
    "unemployed": 0.0,
    "<1": 0.5,
    "1<=X<4": 2.5,
    "4<=X<7": 5.5,
    ">=7": 8.0,
}

CREDIT_HISTORY_DELINQUENCY = {
    "critical/other existing credit": 3,
    "delayed previously": 2,
    "all paid": 1,
    "existing paid": 0,
    "no credits/all paid": 0,
}


def build_monitoring_frame(frame: pd.DataFrame) -> pd.DataFrame:
    employment_years = frame["employment"].astype(str).map(EMPLOYMENT_YEARS).fillna(2.0)
    checking_score = frame["checking_status"].astype(str).map(CHECKING_SCORE).fillna(0.5)
    savings_score = frame["savings_status"].astype(str).map(SAVINGS_SCORE).fillna(0.5)
    delinquency_count = (
        frame["credit_history"].astype(str).map(CREDIT_HISTORY_DELINQUENCY).fillna(0)
    )

    annual_income = (
        frame["credit_amount"] * 14
        + frame["age"] * 210
        + frame["existing_credits"] * 1800
        + employment_years * 1600
    ).clip(lower=18000)

    debt_to_income = (frame["credit_amount"] * frame["duration"] / annual_income / 8).clip(
        lower=0.05, upper=0.95
    )

    credit_utilization = (checking_score * 0.55 + savings_score * 0.45).clip(
        lower=0.05,
        upper=0.98,
    )

    transformed = pd.DataFrame(
        {
            "customer_id": [f"openml-credit-{idx:04d}" for idx in range(1, len(frame) + 1)],
            "age": frame["age"].astype(int),
            "annual_income": annual_income.round(2),
            "debt_to_income": debt_to_income.round(4),
            "credit_utilization": credit_utilization.round(4),
            "num_open_accounts": (frame["existing_credits"] + 1).astype(int),
            "delinquency_count": delinquency_count.astype(int),
            "loan_amount": frame["credit_amount"].astype(float).round(2),
            "employment_years": employment_years.round(1),
            "actual_default": frame["class"].astype(str).eq("bad"),
        }
    )
    return transformed


def main() -> None:
    dataset = fetch_openml(name="credit-g", version=1, as_frame=True)
    prepared = build_monitoring_frame(dataset.frame)

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    full_path = output_dir / "public_credit_scoring_sample.csv"
    baseline_path = output_dir / "public_credit_scoring_baseline.csv"

    prepared.to_csv(full_path, index=False)
    prepared.head(250).drop(columns=["actual_default"]).to_csv(baseline_path, index=False)

    print(f"Saved prepared public sample to {full_path}")
    print(f"Saved prepared baseline snapshot to {baseline_path}")


if __name__ == "__main__":
    main()
