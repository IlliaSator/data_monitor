from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.model_version import ModelVersion
from app.models.retraining_event import RetrainingEvent
from app.schemas.retrain import RetrainingEventResponse, RetrainTriggerResponse


class RetrainService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def trigger_retrain(self, reason: str) -> RetrainTriggerResponse:
        model_version = self._get_active_model()
        if model_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active model version was not found.",
            )

        model_version.retrain_required = True
        existing_description = model_version.description or ""
        model_version.description = f"{existing_description}\nRetrain trigger: {reason}".strip()
        triggered_at = datetime.now(UTC)
        self.db.add(
            RetrainingEvent(
                model_version_id=model_version.id,
                reason=reason,
                triggered_by="manual",
            )
        )
        self.db.commit()
        self.db.refresh(model_version)

        return RetrainTriggerResponse(
            model_version=model_version.version,
            retrain_required=model_version.retrain_required,
            reason=reason,
            triggered_at=triggered_at,
        )

    def mark_retrain_required(self, reason: str, drift_score: float | None = None) -> None:
        model_version = self._get_active_model()
        if model_version is None or model_version.retrain_required:
            return
        model_version.retrain_required = True
        existing_description = model_version.description or ""
        model_version.description = f"{existing_description}\nRetrain trigger: {reason}".strip()
        self.db.add(
            RetrainingEvent(
                model_version_id=model_version.id,
                reason=reason,
                triggered_by="automatic",
                drift_score=drift_score,
            )
        )
        self.db.flush()

    def list_events(self) -> list[RetrainingEventResponse]:
        statement = (
            select(RetrainingEvent, ModelVersion)
            .join(ModelVersion, ModelVersion.id == RetrainingEvent.model_version_id)
            .order_by(RetrainingEvent.created_at.desc())
        )
        rows = self.db.execute(statement).all()
        return [
            RetrainingEventResponse(
                id=event.id,
                model_version=model.version,
                reason=event.reason,
                triggered_by=event.triggered_by,
                drift_score=event.drift_score,
                resolved=event.resolved,
                created_at=event.created_at,
            )
            for event, model in rows
        ]

    def _get_active_model(self) -> ModelVersion | None:
        statement = (
            select(ModelVersion)
            .where(ModelVersion.is_active.is_(True))
            .order_by(ModelVersion.created_at.desc())
        )
        return self.db.scalar(statement)
