from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DriftReport(Base, TimestampMixin):
    __tablename__ = "drift_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    baseline_version: Mapped[str] = mapped_column(String(64), index=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    global_drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    batch = relationship("Batch", back_populates="drift_reports")
    feature_metrics = relationship(
        "FeatureDriftMetric",
        back_populates="drift_report",
        cascade="all, delete-orphan",
    )
    alerts = relationship("Alert", back_populates="drift_report")


class FeatureDriftMetric(Base, TimestampMixin):
    __tablename__ = "feature_drift_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    drift_report_id: Mapped[int] = mapped_column(
        ForeignKey("drift_reports.id", ondelete="CASCADE"),
        index=True,
    )
    feature_name: Mapped[str] = mapped_column(String(128), index=True)
    drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    is_drifted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metric_details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    drift_report = relationship("DriftReport", back_populates="feature_metrics")
