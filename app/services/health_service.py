from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import DB_STATUS_DOWN, DB_STATUS_UP, SERVICE_STATUS_OK
from app.db.session import check_database_connection
from app.models.baseline import Baseline
from app.models.batch import Batch
from app.models.model_version import ModelVersion
from app.schemas.health import HealthResponse


class HealthService:
    def __init__(self, settings: Settings, db: Session | None = None) -> None:
        self.settings = settings
        self.db = db

    def get_health(self) -> HealthResponse:
        is_db_connected = check_database_connection()
        latest_batch = self._get_latest_batch() if is_db_connected else None
        active_model = self._get_active_model_version() if is_db_connected else None
        active_baseline = self._get_active_baseline() if is_db_connected else None

        return HealthResponse(
            status=SERVICE_STATUS_OK,
            version=self.settings.app_version,
            model_version=(
                active_model.version if active_model is not None else self.settings.model_version
            ),
            baseline_version=active_baseline.version if active_baseline is not None else None,
            database_connectivity=DB_STATUS_UP if is_db_connected else DB_STATUS_DOWN,
            last_ingest_at=latest_batch.ingest_completed_at if latest_batch is not None else None,
        )

    def _get_latest_batch(self) -> Batch | None:
        if self.db is None:
            return None
        statement = select(Batch).order_by(Batch.ingest_completed_at.desc())
        return self.db.scalar(statement)

    def _get_active_model_version(self) -> ModelVersion | None:
        if self.db is None:
            return None
        statement = select(ModelVersion).where(ModelVersion.is_active.is_(True))
        return self.db.scalar(statement)

    def _get_active_baseline(self) -> Baseline | None:
        if self.db is None:
            return None
        statement = select(Baseline).where(Baseline.is_active.is_(True))
        return self.db.scalar(statement)


def get_health_service(db: Session) -> HealthService:
    return HealthService(get_settings(), db=db)
