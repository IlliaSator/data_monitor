from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    baseline_version: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    ingest_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ingest_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    quality_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    prediction_logs = relationship(
        "PredictionLog",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    drift_reports = relationship(
        "DriftReport",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
