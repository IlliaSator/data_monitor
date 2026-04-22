# Data Monitor

Production-like ML monitoring service for a credit scoring model. The project is intentionally structured as an interview-ready FastAPI application that demonstrates data drift monitoring, prediction logging, alerting, baseline management, visualization, Dockerized local startup, and CI discipline.

## Why This Project Exists

Most demo ML services stop at model inference. Real production systems need observability around incoming data, model behavior, thresholds, incident visibility, and an operational story for when things start drifting.

This repository focuses on that monitoring layer.

It answers practical interview questions such as:

- How do you detect and persist data drift over time?
- Where do you store prediction logs and monitoring metrics?
- How do you version a baseline instead of hardcoding it in code?
- How do you surface alerts to users and downstream retraining workflows?
- How do you package the service for local development and deployable environments?

## Demo Domain

The service monitors a **credit scoring** model that estimates default risk for loan applicants.

Why this domain works well for demos:

- the features are easy to explain;
- drift examples are intuitive;
- business impact is obvious;
- it maps naturally to alerting and retraining triggers.

Input records contain:

- `customer_id`
- `age`
- `annual_income`
- `debt_to_income`
- `credit_utilization`
- `num_open_accounts`
- `delinquency_count`
- `loan_amount`
- `employment_years`

## What The Service Does

- accepts new application batches through `POST /ingest`
- validates the schema and runs basic data quality checks
- stores batch metadata and prediction logs in PostgreSQL
- compares incoming data against a versioned baseline snapshot
- computes feature-level and global drift scores
- generates and stores an Evidently HTML drift report
- persists alert records when thresholds are exceeded
- exposes alert and metrics history APIs
- renders a dashboard with trend charts and report access
- supports baseline reinitialization and retrain triggers
- starts with Docker Compose and is ready for CI/deploy workflows

## Architecture

High-level flow:

1. `POST /ingest` receives a batch of credit scoring records.
2. Pydantic validates the payload.
3. Quality checks inspect duplicates, missing values, and empty batches.
4. The service creates prediction logs and batch metadata records.
5. Baseline data is loaded from the active baseline artifact.
6. Feature drift is calculated with PSI and summarized into a global drift score.
7. Evidently generates an HTML drift report for the same batch.
8. Drift metrics and feature metrics are saved to PostgreSQL.
9. Alert records are created if thresholds are exceeded.
10. If drift is severe enough, the active model is marked `retrain_required`.

More detail is available in [docs/architecture.md](/d:/Classic%20ML/DeployProjects/data_monitor/docs/architecture.md).

## Project Structure

```text
app/
  api/v1/routes/        FastAPI routes
  core/                 config and logging
  db/                   SQLAlchemy session/base wiring
  dashboard/            Jinja2 template and Plotly chart builders
  jobs/                 APScheduler setup and periodic jobs
  models/               ORM models
  monitoring/           drift and quality logic
  schemas/              request/response models
  services/             business logic
alembic/                migrations
data/                   baseline CSV and runtime baseline snapshots
docs/                   architecture notes
tests/                  unit/service/endpoint tests
```

## Database Schema

Main tables:

- `batches`: ingestion metadata, size, model version, baseline version, warnings
- `prediction_logs`: per-record features and predicted risk outputs
- `drift_reports`: global drift result, report path, flags
- `feature_drift_metrics`: drift scores per feature
- `alerts`: threshold breaches and alert lifecycle state
- `baselines`: versioned baseline metadata and artifact location
- `model_versions`: model registry metadata plus `retrain_required`

Alert status model:

- `open`
- `acknowledged`
- `resolved`

## Endpoints

### Core Monitoring

- `POST /ingest`
  - validates and ingests a batch
  - saves prediction logs
  - computes drift against the active baseline
  - generates an Evidently HTML report
  - returns batch summary, warnings, timestamps, and drift status

- `GET /health`
  - returns app status, version, active model version, active baseline version, database connectivity, and last ingest time

- `GET /drift/report`
  - returns the latest generated Evidently HTML report

### Alerts and Metrics

- `GET /alerts`
  - filters:
    - `severity`
    - `date_from`
    - `date_to`
    - `unresolved_only`

- `GET /metrics/history`
  - filters:
    - `model_version`
    - `baseline_version`
    - `date_from`
    - `date_to`

### Operational Lifecycle

- `POST /baseline/reinitialize`
  - creates a new active baseline from:
    - a dedicated CSV file via `source_csv_path`
    - or the first `N` rows of another dataset via `dataset_path` + `sample_size`

- `POST /retrain/trigger`
  - manually marks the active model as requiring retraining

### Dashboard

- `GET /`
  - shows:
    - drift trend chart
    - top drifted features
    - latest alerts
    - service/model/baseline cards
    - last ingest
    - link to the latest HTML drift report

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

Supported variables:

- `DATABASE_URL`
- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `DRIFT_THRESHOLD`
- `FEATURE_DRIFT_THRESHOLD`
- `ALERT_THRESHOLD`
- `BASELINE_PATH`
- `MODEL_VERSION`
- `REPORTS_DIR`
- `TIMEZONE`
- `CORS_ORIGINS`

## Local Run

### Option 1: Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Available services:

- app: `http://localhost:8000`
- postgres: `localhost:5432`

### Option 2: Local Python

```bash
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

## Migrations

Generate or apply migrations with Alembic:

```bash
alembic upgrade head
```

Offline SQL validation:

```bash
alembic upgrade head --sql
```

## Example Ingest Request

```json
{
  "batch_id": "demo-batch-001",
  "records": [
    {
      "customer_id": "cust-1001",
      "age": 29,
      "annual_income": 54000.0,
      "debt_to_income": 0.41,
      "credit_utilization": 0.57,
      "num_open_accounts": 4,
      "delinquency_count": 1,
      "loan_amount": 16000.0,
      "employment_years": 4.0
    }
  ]
}
```

## How Baseline Management Works

The service does **not** hardcode a baseline in Python code.

Instead:

- the initial baseline is loaded from `BASELINE_PATH`
- baseline metadata is stored in `baselines`
- active baseline snapshots are stored as CSV artifacts
- `POST /baseline/reinitialize` can create a new active baseline version

Example:

```json
{
  "source_csv_path": "data/baseline_credit_scoring.csv",
  "name": "April 2026 baseline"
}
```

Or from another dataset:

```json
{
  "dataset_path": "data/full_reference_dataset.csv",
  "sample_size": 500,
  "name": "Bootstrap baseline"
}
```

## How Drift Is Calculated

This project intentionally separates **reporting** from **stored scoring logic**:

- **PSI** is used for persisted feature drift metrics and the global drift summary
- **Evidently AI** is used to generate the HTML drift report artifact

This is a practical interview-friendly choice:

- the stored metrics are explicit and easy to explain;
- the HTML report is rich and visually compelling;
- thresholds remain under your direct control.

## Alerting Rules

The service uses three threshold concepts:

- `FEATURE_DRIFT_THRESHOLD`
- `DRIFT_THRESHOLD`
- `ALERT_THRESHOLD`

Behavior:

- feature metrics above the feature threshold create feature-level alerts
- global drift above the alert threshold creates a global alert
- severe global drift also marks the active model as `retrain_required`

## Retraining Trigger

Retraining is mocked architecturally but wired into the monitoring flow:

- automatic trigger when global drift exceeds the alert threshold
- manual trigger with `POST /retrain/trigger`
- scheduler reconciliation job for periodic review

This keeps the project realistic without pretending a full training pipeline exists here.

## Background Jobs

APScheduler starts with the application and runs lightweight periodic jobs:

- monitoring snapshot refresh
- retrain flag reconciliation based on latest drift state

The jobs are intentionally simple and readable.

## Dashboard Reading Guide

When you open `/`, the main story should be visible immediately:

- top cards show service status, versions, and last ingest
- line chart shows global drift trend over time
- bar chart highlights the most drifted features
- alert table shows open incidents
- “Open Latest Drift Report” links to the full Evidently HTML artifact

## Testing

Run the test suite:

```bash
pytest -q
```

Current coverage focus:

- drift calculation
- alert generation
- schema validation
- service-layer behavior
- `/health`, `/alerts`, `/metrics/history`

## CI

GitHub Actions workflow includes:

- `ruff check`
- `ruff format --check`
- `pytest`
- Alembic offline migration validation
- Docker image build

## Docker and Deploy Notes

### Docker

The repository includes:

- `Dockerfile`
- `docker-compose.yml`
- PostgreSQL service
- app service
- health checks
- persistent Postgres volume

### Railway / Similar Platforms

Recommended deploy approach:

1. Build the app using the included `Dockerfile`.
2. Provide the same env vars as in `.env.example`.
3. Point `DATABASE_URL` to the managed PostgreSQL instance.
4. Run migrations during deploy:

```bash
alembic upgrade head
```

Typical Railway variables:

- `DATABASE_URL`
- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `BASELINE_PATH`
- `MODEL_VERSION`
- `REPORTS_DIR`
- `TIMEZONE`

Notes:

- baseline and reports directories should be backed by persistent storage if long-lived artifacts matter
- on ephemeral platforms, drift report artifacts may need S3/object storage later

## Example Interview Talking Points

- service-layer architecture keeps business logic out of routes
- SQLAlchemy models normalize monitoring entities
- baseline versions are data artifacts, not hardcoded constants
- alerts and retraining hooks are explicit operational decisions
- dashboard gives a fast product-facing view, while APIs expose machine-readable history
- Docker and CI make the project feel closer to production than a notebook demo

## What Could Be Improved Next

- real model inference integration instead of demo scoring logic
- persistent object storage for reports and baseline artifacts
- richer data quality checks with Pandera
- authentication and role-based alert actions
- alert acknowledgements and resolution endpoints
- model performance monitoring in addition to pure data drift
- async task queue for heavy report generation
