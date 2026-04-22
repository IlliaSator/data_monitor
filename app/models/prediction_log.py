from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PredictionLog(Base, TimestampMixin):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    prediction: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_label: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    features: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    batch = relationship("Batch", back_populates="prediction_logs")
