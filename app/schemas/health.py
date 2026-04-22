from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    model_version: str
    baseline_version: str | None
    database_connectivity: str
    last_ingest_at: datetime | None
