from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.report_service import ReportService, get_report_service

router = APIRouter()


def get_report_service_dependency(
    db: Annotated[Session, Depends(get_db)],
) -> ReportService:
    return get_report_service(db)


@router.get("/drift/report")
def get_latest_report(
    service: Annotated[ReportService, Depends(get_report_service_dependency)],
) -> FileResponse:
    latest_report = service.get_latest_report()
    if latest_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No drift report has been generated yet.",
        )

    return FileResponse(
        latest_report.report_path,
        media_type="text/html",
        filename="latest_drift_report.html",
    )
