# Architecture Notes

## Runtime Flow

```text
Client Batch
   |
   v
POST /ingest
   |
   v
Pydantic validation + quality checks
   |
   v
Batch + prediction_logs persisted
   |
   v
Active baseline loaded from artifact
   |
   v
PSI drift calculation + Evidently report generation
   |
   v
drift_reports + feature_drift_metrics persisted
   |
   +--> alerts persisted
   |
   +--> retrain_required set when severe drift appears
   |
   v
Dashboard / APIs read historical state from PostgreSQL
```

## Main Components

### Routes

- thin FastAPI endpoints
- dependency injection for DB sessions and services
- no direct SQL in handlers

### Services

- orchestrate ingestion, drift, alerts, baseline lifecycle, reports, health, and retraining
- designed to stay testable outside HTTP

### Monitoring Layer

- quality checks
- PSI drift logic
- Evidently HTML report generation

### Persistence Layer

- SQLAlchemy 2.x ORM models
- Alembic migrations
- PostgreSQL as the primary runtime store

### Jobs

- APScheduler for small periodic operational tasks

## Storage Design

### `batches`

Tracks ingestion sessions:

- external batch id
- model version
- baseline version
- row count
- warnings
- quality summary

### `prediction_logs`

Stores per-record prediction outputs and original feature snapshots.

### `drift_reports`

Stores one global drift result per batch:

- global drift score
- drift flags
- report path
- report metadata

### `feature_drift_metrics`

Stores detailed feature-level drift scores for historical analysis and charts.

### `alerts`

Represents operational incidents caused by threshold breaches.

### `baselines`

Represents versioned baseline snapshots and their file artifacts.

### `model_versions`

Represents deployable model metadata and retraining state.

## Design Choices

### PSI + Evidently hybrid

Persisted metrics are calculated with PSI so the logic is explicit and explainable. Evidently is used for HTML reporting because it provides a polished monitoring artifact quickly.

### Baseline as artifact

The baseline lives in CSV artifacts referenced by DB metadata, which makes version changes visible and operationally tractable.

### Retraining as hook, not fake pipeline

This repository does not pretend to train models. It exposes the operational signal that a real training system would consume.
