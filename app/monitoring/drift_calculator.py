from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(slots=True)
class FeatureDriftResult:
    feature_name: str
    drift_score: float
    threshold: float
    is_drifted: bool
    metric_details: dict[str, float | int | bool]


def calculate_population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    bins: int = 10,
) -> float:
    reference_values = reference.astype(float).to_numpy()
    current_values = current.astype(float).to_numpy()

    reference_values = reference_values[~np.isnan(reference_values)]
    current_values = current_values[~np.isnan(current_values)]

    if len(reference_values) == 0 or len(current_values) == 0:
        return 0.0

    quantiles = np.linspace(0, 1, bins + 1)
    bin_edges = np.unique(np.quantile(reference_values, quantiles))
    if len(bin_edges) < 2:
        center = float(reference_values[0])
        bin_edges = np.array([center - 1e-6, center + 1e-6], dtype=float)

    reference_counts, _ = np.histogram(reference_values, bins=bin_edges)
    current_counts, _ = np.histogram(current_values, bins=bin_edges)

    reference_ratio = np.clip(reference_counts / max(len(reference_values), 1), 1e-6, None)
    current_ratio = np.clip(current_counts / max(len(current_values), 1), 1e-6, None)

    psi = np.sum((current_ratio - reference_ratio) * np.log(current_ratio / reference_ratio))
    normalized = min(max(float(psi), 0.0), 1.0)
    return round(normalized, 6)


def calculate_feature_drift(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    threshold: float,
) -> list[FeatureDriftResult]:
    results: list[FeatureDriftResult] = []

    for feature_name in current_data.columns:
        if feature_name not in reference_data.columns:
            continue

        score = calculate_population_stability_index(
            reference_data[feature_name],
            current_data[feature_name],
        )
        results.append(
            FeatureDriftResult(
                feature_name=feature_name,
                drift_score=score,
                threshold=threshold,
                is_drifted=score >= threshold,
                metric_details={
                    "reference_size": int(reference_data[feature_name].notna().sum()),
                    "current_size": int(current_data[feature_name].notna().sum()),
                    "score": score,
                    "threshold": threshold,
                    "method": "psi",
                },
            )
        )

    return results


def calculate_global_drift_score(feature_results: list[FeatureDriftResult]) -> float:
    if not feature_results:
        return 0.0
    score = math.fsum(result.drift_score for result in feature_results) / len(feature_results)
    return round(score, 6)
