from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.retrain import (
    RetrainingEventResponse,
    RetrainTriggerRequest,
    RetrainTriggerResponse,
)
from app.services.retrain_service import RetrainService

router = APIRouter()


def get_retrain_service(db: Annotated[Session, Depends(get_db)]) -> RetrainService:
    return RetrainService(db=db, settings=get_settings())


@router.post("/retrain/trigger", response_model=RetrainTriggerResponse)
def trigger_retrain(
    payload: RetrainTriggerRequest,
    service: Annotated[RetrainService, Depends(get_retrain_service)],
) -> RetrainTriggerResponse:
    return service.trigger_retrain(payload.reason)


@router.get("/retrain/events", response_model=list[RetrainingEventResponse])
def list_retraining_events(
    service: Annotated[RetrainService, Depends(get_retrain_service)],
) -> list[RetrainingEventResponse]:
    return service.list_events()
