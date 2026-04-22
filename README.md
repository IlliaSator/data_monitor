# Data Monitor

Production-like ML monitoring service for a credit scoring demo model. The project is designed to be interview-ready: clear service boundaries, PostgreSQL persistence, drift monitoring, alerts, dashboarding, Dockerized local startup, and CI-friendly tooling.

## Demo Case

The service monitors a credit scoring model that predicts default risk for loan applicants. This domain works well in interviews because the features are intuitive, drift is easy to explain, and the monitoring story is realistic:

- incoming application batches are ingested through an API;
- predictions and batch metadata are stored for auditability;
- batches are compared against a versioned baseline;
- drift metrics and alerts are persisted and visualized.

## Planned Capabilities

- `POST /ingest` for batch ingestion and prediction logging
- drift reports with Evidently
- PostgreSQL storage for batches, metrics, alerts, baselines, and model versions
- dashboard with metric history and top drifted features
- alerting thresholds and retraining trigger hooks
- Docker Compose local stack and Railway-friendly deploy setup
- tests, linting, and GitHub Actions CI

## Current Status

Initial bootstrap is in place:

- FastAPI application scaffold
- environment-based config
- health endpoint
- logging setup
- Dockerfile and `docker-compose.yml`

More functionality will be added in small atomic commits.
