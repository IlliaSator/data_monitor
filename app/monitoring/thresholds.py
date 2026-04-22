from dataclasses import dataclass


@dataclass(slots=True)
class DriftThresholds:
    global_threshold: float
    feature_threshold: float
    alert_threshold: float
