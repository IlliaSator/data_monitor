from enum import StrEnum


class AlertSeverity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class AlertStatus(StrEnum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"
