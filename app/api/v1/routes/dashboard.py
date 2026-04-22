from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dashboard.charts import build_global_drift_chart, build_top_feature_chart
from app.db.session import get_db
from app.services.alert_service import AlertService
from app.services.metrics_service import MetricsService
from app.services.report_service import get_report_service
from app.services.retrain_service import RetrainService

router = APIRouter()
templates = Jinja2Templates(directory="app/dashboard/templates")


def get_dashboard_context(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    settings = get_settings()
    metrics_service = MetricsService(db)
    alert_service = AlertService(db)
    report_service = get_report_service(db)
    retrain_service = RetrainService(db, settings)
    history = metrics_service.get_history()
    alerts = alert_service.list_alerts(unresolved_only=True)
    retraining_events = retrain_service.list_events()
    latest_report = report_service.get_latest_report()

    latest_global = history.global_metrics[0] if history.global_metrics else None
    latest_performance = history.performance_metrics[0] if history.performance_metrics else None
    last_ingest_at = latest_global.created_at if latest_global is not None else None

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "model_version": latest_global.model_version if latest_global else settings.model_version,
        "service_status": "Monitoring active",
        "last_ingest_at": last_ingest_at,
        "latest_report_url": "/drift/report" if latest_report else None,
        "global_drift_chart": build_global_drift_chart(history.global_metrics),
        "top_feature_chart": build_top_feature_chart(history.feature_metrics),
        "alerts": alerts[:10],
        "top_features": sorted(
            history.feature_metrics,
            key=lambda item: item.drift_score,
            reverse=True,
        )[:5],
        "latest_global_score": latest_global.global_drift_score if latest_global else None,
        "latest_baseline_version": latest_global.baseline_version if latest_global else None,
        "latest_accuracy": latest_performance.accuracy if latest_performance else None,
        "latest_roc_auc": latest_performance.roc_auc if latest_performance else None,
        "performance_tracked_batches": len(history.performance_metrics),
        "retraining_events": retraining_events[:5],
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    context: Annotated[dict, Depends(get_dashboard_context)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, **context},
    )
