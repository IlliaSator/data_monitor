from fastapi import APIRouter

from app.api.v1.routes.alerts import router as alerts_router
from app.api.v1.routes.dashboard import router as dashboard_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ingest import router as ingest_router
from app.api.v1.routes.metrics import router as metrics_router

api_router = APIRouter()
api_router.include_router(alerts_router, tags=["alerts"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(ingest_router, tags=["ingest"])
api_router.include_router(metrics_router, tags=["metrics"])
