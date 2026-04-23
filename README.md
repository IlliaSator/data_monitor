# Data Monitor

Production-like ML monitoring service for a credit scoring use case. The project is designed as a middle to middle+ ML/MLOps interview showcase: it demonstrates ingestion, prediction logging, data drift, model performance monitoring, alert lifecycle, baseline management, retraining triggers, PostgreSQL persistence, dashboarding, Docker, migrations, tests, CI, and deployment notes.

## English

### What Problem This Solves

Many ML demos stop after returning a prediction. Real services need to answer harder operational questions:

- Are incoming features drifting away from the training or reference baseline?
- Are predictions and metrics persisted for audit and debugging?
- Can we inspect metric history and alerts without reading logs?
- Can a baseline be versioned and refreshed without changing source code?
- Is there a clear signal that retraining should happen?

This service focuses on that production monitoring layer.

### Domain

The demo domain is **credit scoring**. The API accepts batches of loan applicant records and estimates default risk. This domain is useful for interviews because the features are intuitive and drift scenarios are easy to explain.

Core features:

- `age`
- `annual_income`
- `debt_to_income`
- `credit_utilization`
- `num_open_accounts`
- `delinquency_count`
- `loan_amount`
- `employment_years`
- optional `actual_default` for model performance monitoring

### Data Strategy

The repository supports two data modes:

- Demo baseline: `data/baseline_credit_scoring.csv`
- Public dataset flow: OpenML `credit-g`, prepared through `scripts/prepare_public_dataset.py`

The public dataset is transformed into the API contract used by this service and saved as:

- `data/public_credit_scoring_sample.csv`
- `data/public_credit_scoring_baseline.csv`

Generate it with:

```bash
python scripts/prepare_public_dataset.py
```

This keeps the project honest: the service can run with a small built-in demo baseline, while also having a reproducible public-data path for portfolio and interview discussions.

Sources:

- OpenML dataset: `credit-g` (`https://api.openml.org/d/31`)
- scikit-learn API: `fetch_openml` (`https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_openml.html`)

### Main Capabilities

- `POST /ingest` accepts JSON batches, validates schema, stores batch metadata and prediction logs
- data quality checks catch empty batches, missing values, duplicate rows, and schema issues
- feature-level drift is calculated with PSI
- Evidently generates an HTML drift report for every ingested batch
- PostgreSQL stores batches, predictions, drift reports, feature drift metrics, performance metrics, alerts, baselines, model versions, and retraining events
- `GET /alerts` lists threshold breaches
- `PATCH /alerts/{alert_id}` updates alert status to `open`, `acknowledged`, or `resolved`
- `GET /metrics/history` returns drift and performance history
- `GET /drift/report` returns the latest Evidently HTML report
- `POST /baseline/reinitialize` creates a new active baseline snapshot
- `POST /retrain/trigger` manually marks the active model as needing retrain
- `GET /retrain/events` returns retraining trigger history
- `/` renders a dashboard with drift trend, top drifted features, alerts, model performance cards, and retraining events
- APScheduler runs lightweight periodic monitoring jobs

### Architecture

```text
Client batch
  -> FastAPI route
  -> Pydantic validation
  -> quality checks
  -> service layer
  -> prediction logs + batch metadata
  -> active baseline loading
  -> PSI drift calculation
  -> Evidently report generation
  -> metrics + alerts + retraining events
  -> PostgreSQL
  -> dashboard and API history
```

Code organization:

```text
app/
  api/v1/routes/     FastAPI endpoints
  core/              config and logging
  db/                SQLAlchemy session and model imports
  dashboard/         Jinja2 template and Plotly charts
  jobs/              APScheduler jobs
  models/            SQLAlchemy ORM models
  monitoring/        drift and quality logic
  schemas/           Pydantic request/response schemas
  services/          business logic
alembic/             migrations
data/                demo and public prepared data
docs/                architecture notes
scripts/             dataset and deploy helper scripts
tests/               unit, service, and endpoint tests
```

### Database Tables

- `batches`
- `prediction_logs`
- `drift_reports`
- `feature_drift_metrics`
- `performance_metrics`
- `alerts`
- `baselines`
- `model_versions`
- `retraining_events`

This is intentionally more realistic than a flat metrics table: monitoring entities are normalized and can be queried independently.

### Endpoints

```text
GET    /
GET    /health
POST   /ingest
GET    /alerts
PATCH  /alerts/{alert_id}
GET    /metrics/history
GET    /drift/report
POST   /baseline/reinitialize
POST   /retrain/trigger
GET    /retrain/events
```

### Local Run

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Apply migrations manually if running outside Docker:

```bash
alembic upgrade head
```

Run locally without Docker:

```bash
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

### Example Ingest Request

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
      "employment_years": 4.0,
      "actual_default": false
    }
  ]
}
```

### Baseline Management

The baseline is not hardcoded in Python. It is versioned as a data artifact and referenced in the `baselines` table.

Example:

```json
{
  "source_csv_path": "data/public_credit_scoring_baseline.csv",
  "name": "OpenML credit-g baseline"
}
```

Or initialize from the first rows of another CSV:

```json
{
  "dataset_path": "data/public_credit_scoring_sample.csv",
  "sample_size": 250,
  "name": "Bootstrap public baseline"
}
```

### Drift and Performance Monitoring

The service tracks two related but different things:

- Data drift: feature distribution shift versus the active baseline
- Model performance: accuracy, precision, recall, F1, ROC AUC, and positive rate when `actual_default` is provided

This distinction is important in interviews. Drift can happen before labels arrive; performance monitoring becomes possible after labels are available.

### Alerts and Retraining

Alerts are created when feature or global drift thresholds are exceeded. Alerts have lifecycle states:

- `open`
- `acknowledged`
- `resolved`

Severe drift automatically creates a retraining event and marks the active model as `retrain_required`. Manual retraining triggers are also stored in `retraining_events`.

### Docker and Deploy

The Docker image uses `scripts/start.sh`, which applies Alembic migrations before starting Uvicorn:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

This is suitable for Railway-like platforms where the app container starts directly from the Dockerfile.

Recommended Railway variables:

- `DATABASE_URL`
- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `DRIFT_THRESHOLD`
- `FEATURE_DRIFT_THRESHOLD`
- `ALERT_THRESHOLD`
- `BASELINE_PATH`
- `MODEL_VERSION`
- `REPORTS_DIR`
- `TIMEZONE`
- `CORS_ORIGINS`

### Tests and CI

Run locally:

```bash
ruff check .
pytest -q
alembic upgrade head --sql
```

GitHub Actions runs:

- lint
- format check
- tests
- Alembic SQL validation
- Docker image build

### Why This Is Middle / Middle+ Level

This project goes beyond a simple FastAPI prediction endpoint. It shows:

- modular service-layer architecture
- normalized monitoring storage
- versioned baselines
- data drift and model performance monitoring
- alert lifecycle
- retraining event tracking
- Dockerized runtime
- migration-aware startup
- tests and CI
- clear dashboard for non-code inspection

Remaining realistic future improvements:

- real trained model artifact instead of demo scoring logic
- object storage for reports and baselines
- authentication and role-based alert actions
- async worker queue for heavy report generation
- richer data validation with Pandera

## Русский

### Какую проблему решает проект

Многие ML demo заканчиваются на endpoint, который возвращает prediction. В реальном сервисе нужно отвечать на более важные эксплуатационные вопросы:

- Дрейфуют ли входные признаки относительно baseline?
- Сохраняются ли predictions и monitoring metrics для аудита и отладки?
- Можно ли посмотреть историю метрик и alerts без чтения логов?
- Можно ли версионировать baseline и обновлять его без изменения кода?
- Есть ли понятный сигнал, что модели нужен retraining?

Этот проект показывает именно production monitoring слой вокруг ML модели.

### Домен

Demo-case: **credit scoring**. API принимает батчи заявок на кредит и оценивает риск дефолта. Этот домен хорошо подходит для собеседований, потому что признаки понятны, а drift-сценарии легко объяснить.

Основные признаки:

- `age`
- `annual_income`
- `debt_to_income`
- `credit_utilization`
- `num_open_accounts`
- `delinquency_count`
- `loan_amount`
- `employment_years`
- optional `actual_default` для monitoring качества модели

### Стратегия по данным

В репозитории есть два режима данных:

- demo baseline: `data/baseline_credit_scoring.csv`
- публичный dataset flow: OpenML `credit-g`, подготовка через `scripts/prepare_public_dataset.py`

Публичный dataset преобразуется в контракт API этого сервиса и сохраняется как:

- `data/public_credit_scoring_sample.csv`
- `data/public_credit_scoring_baseline.csv`

Сгенерировать данные можно так:

```bash
python scripts/prepare_public_dataset.py
```

Это честный вариант для портфолио: сервис может работать с маленьким demo baseline, но также имеет воспроизводимый путь подготовки публичных данных.

Источники:

- OpenML dataset: `credit-g` (`https://api.openml.org/d/31`)
- scikit-learn API: `fetch_openml` (`https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_openml.html`)

### Основные возможности

- `POST /ingest` принимает JSON batch, валидирует схему, сохраняет batch metadata и prediction logs
- data quality checks ловят empty batch, missing values, duplicated rows и schema issues
- feature-level drift считается через PSI
- Evidently генерирует HTML drift report для каждого ingest
- PostgreSQL хранит batches, predictions, drift reports, feature metrics, performance metrics, alerts, baselines, model versions и retraining events
- `GET /alerts` возвращает нарушения порогов
- `PATCH /alerts/{alert_id}` переводит alert в `open`, `acknowledged` или `resolved`
- `GET /metrics/history` возвращает историю drift и performance metrics
- `GET /drift/report` возвращает последний Evidently HTML report
- `POST /baseline/reinitialize` создает новый active baseline snapshot
- `POST /retrain/trigger` вручную помечает active model как needing retrain
- `GET /retrain/events` возвращает историю retraining triggers
- `/` показывает dashboard с drift trend, top drifted features, alerts, performance cards и retraining events
- APScheduler запускает легкие periodic monitoring jobs

### Архитектура

```text
Client batch
  -> FastAPI route
  -> Pydantic validation
  -> quality checks
  -> service layer
  -> prediction logs + batch metadata
  -> active baseline loading
  -> PSI drift calculation
  -> Evidently report generation
  -> metrics + alerts + retraining events
  -> PostgreSQL
  -> dashboard and API history
```

Структура проекта:

```text
app/
  api/v1/routes/     FastAPI endpoints
  core/              config and logging
  db/                SQLAlchemy session and model imports
  dashboard/         Jinja2 template and Plotly charts
  jobs/              APScheduler jobs
  models/            SQLAlchemy ORM models
  monitoring/        drift and quality logic
  schemas/           Pydantic request/response schemas
  services/          business logic
alembic/             migrations
data/                demo and public prepared data
docs/                architecture notes
scripts/             dataset and deploy helper scripts
tests/               unit, service, and endpoint tests
```

### Таблицы БД

- `batches`
- `prediction_logs`
- `drift_reports`
- `feature_drift_metrics`
- `performance_metrics`
- `alerts`
- `baselines`
- `model_versions`
- `retraining_events`

Это выглядит взрослее, чем одна плоская таблица metrics: сущности мониторинга нормализованы и их можно независимо фильтровать.

### Endpoints

```text
GET    /
GET    /health
POST   /ingest
GET    /alerts
PATCH  /alerts/{alert_id}
GET    /metrics/history
GET    /drift/report
POST   /baseline/reinitialize
POST   /retrain/trigger
GET    /retrain/events
```

### Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

Открыть:

```text
http://localhost:8000
```

Если запускаешь без Docker, применить migrations:

```bash
alembic upgrade head
```

Запуск локально через Python:

```bash
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

### Пример ingest request

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
      "employment_years": 4.0,
      "actual_default": false
    }
  ]
}
```

### Baseline management

Baseline не захардкожен в Python. Он хранится как версионированный data artifact и описывается в таблице `baselines`.

Пример:

```json
{
  "source_csv_path": "data/public_credit_scoring_baseline.csv",
  "name": "OpenML credit-g baseline"
}
```

Или baseline из первых строк другого CSV:

```json
{
  "dataset_path": "data/public_credit_scoring_sample.csv",
  "sample_size": 250,
  "name": "Bootstrap public baseline"
}
```

### Drift и performance monitoring

Сервис отслеживает две разные вещи:

- Data drift: сдвиг распределений признаков относительно active baseline
- Model performance: accuracy, precision, recall, F1, ROC AUC и positive rate, если в batch передан `actual_default`

Это важное различие для собеседований. Drift можно считать до появления labels, а performance monitoring становится возможен после появления фактического target.

### Alerts и retraining

Alerts создаются, если превышены feature-level или global thresholds. У alert есть lifecycle:

- `open`
- `acknowledged`
- `resolved`

Сильный drift автоматически создает retraining event и помечает active model как `retrain_required`. Ручные retraining triggers также сохраняются в `retraining_events`.

### Docker и deploy

Docker image использует `scripts/start.sh`, который применяет Alembic migrations перед запуском Uvicorn:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Это подходит для Railway-like платформ, где контейнер стартует напрямую из Dockerfile.

Рекомендуемые Railway variables:

- `DATABASE_URL`
- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `DRIFT_THRESHOLD`
- `FEATURE_DRIFT_THRESHOLD`
- `ALERT_THRESHOLD`
- `BASELINE_PATH`
- `MODEL_VERSION`
- `REPORTS_DIR`
- `TIMEZONE`
- `CORS_ORIGINS`

### Тесты и CI

Локально:

```bash
ruff check .
pytest -q
alembic upgrade head --sql
```

GitHub Actions запускает:

- lint
- format check
- tests
- Alembic SQL validation
- Docker image build

### Почему это уровень middle / middle+

Проект уже не выглядит как простой FastAPI endpoint для prediction. Он показывает:

- modular service-layer architecture
- normalized monitoring storage
- versioned baselines
- data drift и model performance monitoring
- alert lifecycle
- retraining event tracking
- Dockerized runtime
- migration-aware startup
- tests and CI
- dashboard, который можно открыть и быстро понять состояние сервиса

Что можно улучшить дальше:

- подключить настоящий trained model artifact вместо demo scoring logic
- вынести reports и baselines в object storage
- добавить authentication и role-based alert actions
- вынести тяжелую генерацию reports в async worker queue
- расширить data validation через Pandera
