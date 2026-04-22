import pandas as pd

from app.monitoring.drift_calculator import (
    calculate_feature_drift,
    calculate_global_drift_score,
    calculate_population_stability_index,
)


def test_population_stability_index_is_zero_for_identical_distributions():
    reference = pd.Series([1, 2, 3, 4, 5, 6])
    current = pd.Series([1, 2, 3, 4, 5, 6])

    score = calculate_population_stability_index(reference, current)

    assert score == 0.0


def test_feature_drift_and_global_score_are_bounded():
    reference = pd.DataFrame(
        {
            "annual_income": [45000, 50000, 55000, 60000, 65000],
            "credit_utilization": [0.2, 0.25, 0.3, 0.28, 0.32],
        }
    )
    current = pd.DataFrame(
        {
            "annual_income": [15000, 18000, 20000, 23000, 25000],
            "credit_utilization": [0.7, 0.75, 0.8, 0.78, 0.82],
        }
    )

    feature_results = calculate_feature_drift(reference, current, threshold=0.4)
    global_score = calculate_global_drift_score(feature_results)

    assert len(feature_results) == 2
    assert all(0.0 <= result.drift_score <= 1.0 for result in feature_results)
    assert 0.0 <= global_score <= 1.0
    assert any(result.is_drifted for result in feature_results)
