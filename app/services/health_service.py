from app.core.config import Settings, get_settings
from app.core.constants import DB_STATUS_DOWN, DB_STATUS_UP, SERVICE_STATUS_OK
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_health(self) -> HealthResponse:
        is_db_connected = check_database_connection()
        return HealthResponse(
            status=SERVICE_STATUS_OK,
            version=self.settings.app_version,
            model_version=self.settings.model_version,
            baseline_version=None,
            database_connectivity=DB_STATUS_UP if is_db_connected else DB_STATUS_DOWN,
            last_ingest_at=None,
        )


def get_health_service() -> HealthService:
    return HealthService(get_settings())
