from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.baseline import BaselineReinitializeRequest, BaselineResponse
from app.services.baseline_service import BaselineService

router = APIRouter()


def get_baseline_service(db: Annotated[Session, Depends(get_db)]) -> BaselineService:
    return BaselineService(db=db, settings=get_settings())


@router.post("/baseline/reinitialize", response_model=BaselineResponse)
def reinitialize_baseline(
    payload: BaselineReinitializeRequest,
    service: Annotated[BaselineService, Depends(get_baseline_service)],
) -> BaselineResponse:
    return service.reinitialize_baseline(
        source_csv_path=payload.source_csv_path,
        dataset_path=payload.dataset_path,
        sample_size=payload.sample_size,
        name=payload.name,
        description=payload.description,
    )
