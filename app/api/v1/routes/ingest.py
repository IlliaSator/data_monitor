from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingestion_service import IngestionService, get_ingestion_service

router = APIRouter()


def get_ingestion_service_dependency(
    db: Annotated[Session, Depends(get_db)],
) -> IngestionService:
    return get_ingestion_service(db)


@router.post("/ingest", response_model=IngestResponse)
def ingest_batch(
    payload: IngestRequest,
    service: Annotated[IngestionService, Depends(get_ingestion_service_dependency)],
) -> IngestResponse:
    return service.ingest_batch(payload)
