from pathlib import Path

from app.core.config import Settings
from app.models.baseline import Baseline
from app.models.batch import Batch
from app.models.drift_report import DriftReport
from app.models.model_version import ModelVersion
from app.models.prediction_log import PredictionLog
from app.schemas.baseline import BaselineReinitializeRequest
from app.schemas.ingest import IngestRequest
from app.services.baseline_service import BaselineService
from app.services.ingestion_service import IngestionService
from app.services.retrain_service import RetrainService


def test_ingestion_service_persists_batch_predictions_and_drift(db_session, sample_batch, tmp_path):
    settings = Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        BASELINE_PATH=str(Path("data/baseline_credit_scoring.csv").resolve()),
        REPORTS_DIR=str(tmp_path / "reports"),
        MODEL_VERSION="credit_scoring_test_v1",
    )
    payload = IngestRequest.model_validate(sample_batch)

    response = IngestionService(db_session, settings).ingest_batch(payload)

    assert response.size == 2
    assert db_session.query(Batch).count() == 1
    assert db_session.query(PredictionLog).count() == 2
    assert db_session.query(DriftReport).count() == 1
    assert db_session.query(ModelVersion).one().retrain_required is True


def test_baseline_service_reinitializes_active_baseline(db_session):
    settings = Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        BASELINE_PATH=str(Path("data/baseline_credit_scoring.csv").resolve()),
    )
    service = BaselineService(db_session, settings)
    payload = BaselineReinitializeRequest(
        source_csv_path=str(Path("data/baseline_credit_scoring.csv").resolve()),
        name="Interview baseline",
    )

    baseline = service.reinitialize_baseline(
        source_csv_path=payload.source_csv_path,
        dataset_path=payload.dataset_path,
        sample_size=payload.sample_size,
        name=payload.name,
        description=payload.description,
    )

    active_baseline = db_session.query(Baseline).filter(Baseline.is_active.is_(True)).one()
    assert baseline.version == active_baseline.version
    assert active_baseline.row_count > 0


def test_retrain_service_sets_flag_for_active_model(db_session):
    model = ModelVersion(
        version="credit_scoring_v1",
        name="Credit scoring",
        is_active=True,
    )
    db_session.add(model)
    db_session.commit()

    response = RetrainService(
        db_session,
        Settings(DATABASE_URL="sqlite+pysqlite:///:memory:", MODEL_VERSION="credit_scoring_v1"),
    ).trigger_retrain("Manual trigger for testing")

    db_session.refresh(model)
    assert response.retrain_required is True
    assert model.retrain_required is True
