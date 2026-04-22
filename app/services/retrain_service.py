from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.model_version import ModelVersion
from app.schemas.retrain import RetrainTriggerResponse


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
        model_version.description = (
            f"{existing_description}\nRetrain trigger: {reason}".strip()
        )
        triggered_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(model_version)

        return RetrainTriggerResponse(
            model_version=model_version.version,
            retrain_required=model_version.retrain_required,
            reason=reason,
            triggered_at=triggered_at,
        )

    def mark_retrain_required(self, reason: str) -> None:
        model_version = self._get_active_model()
        if model_version is None or model_version.retrain_required:
            return
        model_version.retrain_required = True
        existing_description = model_version.description or ""
        model_version.description = (
            f"{existing_description}\nRetrain trigger: {reason}".strip()
        )
        self.db.flush()

    def _get_active_model(self) -> ModelVersion | None:
        statement = (
            select(ModelVersion)
            .where(ModelVersion.is_active.is_(True))
            .order_by(ModelVersion.created_at.desc())
        )
        return self.db.scalar(statement)
