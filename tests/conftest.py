from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.base  # noqa: F401
from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def sample_batch() -> dict:
    return {
        "batch_id": "test-batch-001",
        "records": [
            {
                "customer_id": "cust-1",
                "age": 34,
                "annual_income": 72000.0,
                "debt_to_income": 0.31,
                "credit_utilization": 0.42,
                "num_open_accounts": 5,
                "delinquency_count": 1,
                "loan_amount": 12000.0,
                "employment_years": 6.0,
            },
            {
                "customer_id": "cust-2",
                "age": 28,
                "annual_income": 43000.0,
                "debt_to_income": 0.55,
                "credit_utilization": 0.71,
                "num_open_accounts": 3,
                "delinquency_count": 2,
                "loan_amount": 21000.0,
                "employment_years": 2.0,
            },
        ],
    }


@pytest.fixture()
def client(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    reports_dir = tmp_path / "reports"
    baseline_path = Path("data/baseline_credit_scoring.csv").resolve()

    monkeypatch.setenv("BASELINE_PATH", str(baseline_path))
    monkeypatch.setenv("REPORTS_DIR", str(reports_dir))
    monkeypatch.setenv("MODEL_VERSION", "credit_scoring_test_v1")
    get_settings.cache_clear()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.services.health_service.check_database_connection", lambda: True)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    shutil.rmtree(reports_dir, ignore_errors=True)
