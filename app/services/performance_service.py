from __future__ import annotations

from collections.abc import Sequence

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.performance_metric import PerformanceMetric
from app.schemas.performance import PerformanceMetricResponse


class PerformanceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_batch_metrics(
        self,
        *,
        batch: Batch,
        predictions: Sequence[float],
        actual_labels: Sequence[bool],
        model_version: str,
    ) -> PerformanceMetric:
        predicted_classes = [score >= 0.5 for score in predictions]
        labels = [int(label) for label in actual_labels]
        predicted = [int(label) for label in predicted_classes]
        positive_rate = sum(labels) / len(labels)

        roc_auc = None
        if len(set(labels)) > 1:
            roc_auc = round(float(roc_auc_score(labels, predictions)), 4)

        metric = PerformanceMetric(
            batch_id=batch.id,
            model_version=model_version,
            sample_size=len(labels),
            positive_rate=round(float(positive_rate), 4),
            accuracy=round(float(accuracy_score(labels, predicted)), 4),
            precision=round(float(precision_score(labels, predicted, zero_division=0)), 4),
            recall=round(float(recall_score(labels, predicted, zero_division=0)), 4),
            f1_score=round(float(f1_score(labels, predicted, zero_division=0)), 4),
            roc_auc=roc_auc,
            performance_below_threshold=(roc_auc is not None and roc_auc < 0.7),
        )
        self.db.add(metric)
        self.db.flush()
        return metric

    def list_history(self) -> list[PerformanceMetricResponse]:
        statement: Select[tuple[PerformanceMetric, Batch]] = (
            select(PerformanceMetric, Batch)
            .join(Batch, Batch.id == PerformanceMetric.batch_id)
            .order_by(PerformanceMetric.created_at.desc())
        )
        rows = self.db.execute(statement).all()
        return [
            PerformanceMetricResponse(
                created_at=metric.created_at,
                batch_id=batch.external_id,
                model_version=metric.model_version,
                sample_size=metric.sample_size,
                positive_rate=metric.positive_rate,
                accuracy=metric.accuracy,
                precision=metric.precision,
                recall=metric.recall,
                f1_score=metric.f1_score,
                roc_auc=metric.roc_auc,
                performance_below_threshold=metric.performance_below_threshold,
            )
            for metric, batch in rows
        ]
