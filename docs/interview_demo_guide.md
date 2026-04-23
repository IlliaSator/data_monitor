# Data Monitor: описание проекта и сценарий демонстрации

## Короткое описание

`Data Monitor` - production-like ML monitoring service для credit scoring. Он показывает не только prediction endpoint, а полный monitoring layer вокруг ML-модели: batch ingestion, валидацию данных, prediction logs, PostgreSQL storage, drift metrics, Evidently HTML reports, alerts, baseline management, performance monitoring, retraining triggers, dashboard, Docker, Alembic migrations, tests и CI.

Проект хорошо позиционировать как middle/middle+ ML/MLOps demo: он небольшой, но демонстрирует реальные эксплуатационные вопросы, которые появляются после деплоя модели.

## Что именно здесь production-like

- API написан на FastAPI, бизнес-логика вынесена в service layer.
- Входные batch records валидируются через Pydantic v2.
- Перед drift calculation выполняются data quality checks: empty batch, missing values, duplicate rows, schema issues.
- Prediction logs, batches, drift reports, feature-level metrics, alerts, baselines, model versions, performance metrics и retraining events сохраняются в PostgreSQL.
- Схема БД управляется через Alembic migrations.
- Baseline не захардкожен в Python: он версионируется и может быть переинициализирован через endpoint.
- Drift считается относительно active baseline, feature-level metrics сохраняются отдельно.
- Evidently генерирует HTML drift report.
- Alerts имеют lifecycle: `open`, `acknowledged`, `resolved`.
- Есть retraining trigger: сильный drift помечает active model как `retrain_required`.
- Dashboard показывает drift trend, top drifted features, alerts, performance cards и retraining events.
- Проект запускается через Docker Compose и имеет GitHub Actions для lint, tests, migration SQL check и Docker build.

## Модель и данные

Домен: credit scoring.

Источник данных: публичный OpenML `credit-g`, подготовленный скриптом `scripts/prepare_public_dataset.py` под API-контракт сервиса.

Модель: сохранённый scikit-learn artifact `models/credit_scoring_model.joblib`.

Training script: `scripts/train_credit_model.py`.

Runtime setting: `MODEL_PATH=models/credit_scoring_model.joblib`.

Модель - это `StandardScaler` + `LogisticRegression`, обученная на подготовленном public credit dataset. Holdout ROC AUC около `0.77`, что нормально для компактного демонстрационного credit scoring кейса. Если artifact отсутствует, сервис использует deterministic fallback scorer, чтобы demo не ломалось в новой среде.

## Как демонстрировать за 5-7 минут

1. Открыть README и показать screenshots.
2. Открыть dashboard: `http://localhost:8000/`.
3. Показать status cards: service status, model version, baseline version, last ingest, accuracy/ROC AUC.
4. Показать drift trend и top drifted features.
5. Показать таблицу alerts и объяснить thresholds.
6. Открыть Evidently report через кнопку `Open Latest Drift Report`.
7. Открыть Swagger: `http://localhost:8000/docs`.
8. Показать endpoints: `/ingest`, `/alerts`, `/metrics/history`, `/baseline/reinitialize`, `/retrain/trigger`, `/health`.
9. Показать, что данные и метрики сохраняются в PostgreSQL, а не живут только в памяти.
10. В конце показать tests/CI: `pytest`, `ruff`, Alembic, GitHub Actions.

## Как подготовить демо локально

Запуск:

```bash
cp .env.example .env
docker compose up --build
```

Если нужно быстро наполнить dashboard историей:

```bash
python scripts/seed_demo_history.py
```

Если нужно переобучить model artifact:

```bash
python scripts/prepare_public_dataset.py
python scripts/train_credit_model.py
```

Полезные URL:

- Dashboard: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Alerts: `http://localhost:8000/alerts`
- Metrics history: `http://localhost:8000/metrics/history`
- Latest Evidently report: `http://localhost:8000/drift/report`

## Как объяснять архитектуру

Основной поток:

```text
JSON batch
  -> FastAPI route
  -> Pydantic validation
  -> data quality checks
  -> model prediction
  -> prediction logs + batch metadata
  -> active baseline loading
  -> PSI drift calculation
  -> Evidently HTML report
  -> drift metrics + alerts + retraining events
  -> PostgreSQL
  -> dashboard / API history
```

Ключевая идея: endpoint `/ingest` не просто возвращает predictions. Он создаёт audit trail и monitoring artifacts, которые потом можно анализировать через dashboard и API.

## Частые вопросы интервьюера и ответы

**Почему FastAPI?**

FastAPI хорошо подходит для ML-serving и internal monitoring APIs: typed contracts, OpenAPI/Swagger из коробки, dependency injection, хорошая интеграция с Pydantic.

**Почему PostgreSQL, а не файлы?**

Prediction logs, alerts, metrics history и baseline metadata должны быть queryable и auditable. PostgreSQL даёт нормализованную схему, индексы, миграции и удобную интеграцию с dashboard/API.

**Что такое data drift в этом проекте?**

Это изменение распределения входных признаков относительно active baseline. Сервис считает feature-level PSI и global drift score, а Evidently report даёт дополнительный HTML-анализ.

**Чем data drift отличается от model drift/performance degradation?**

Data drift можно считать без target labels: сравниваем feature distributions. Model performance monitoring требует `actual_default`, поэтому accuracy/precision/recall/F1/ROC AUC считаются только когда фактические labels уже пришли.

**Почему PSI?**

PSI простой, объяснимый и часто используется в credit scoring/risk monitoring. Для demo он хорош тем, что легко объясняется и даёт feature-level scores.

**Почему Evidently иногда пишет "Dataset Drift is NOT detected", хотя dashboard показывает alerts?**

Dashboard использует наш global PSI threshold и alert threshold. Evidently может принимать решение по доле drifted columns и своему dataset-level threshold. Это нормальная ситуация: в production часто есть несколько drift signals, а alert policy задаётся отдельно бизнесом/командой.

**Модель настоящая или demo scoring?**

Сейчас есть настоящий scikit-learn artifact: `models/credit_scoring_model.joblib`, обученный через `scripts/train_credit_model.py` на подготовленном OpenML `credit-g`. Rule-based scoring оставлен только как fallback, если artifact отсутствует.

**Почему LogisticRegression, а не LightGBM/XGBoost?**

Для interview demo важнее monitoring architecture, воспроизводимость и объяснимость. LogisticRegression быстрее обучается, проще объясняется, хорошо подходит для credit scoring baseline. В roadmap можно добавить model registry и более сильные модели.

**Почему baseline хранится как artifact?**

Baseline - это reference distribution. Его нужно версионировать отдельно от кода, потому что baseline может обновляться после retraining или после согласованного production window.

**Что происходит при сильном drift?**

Создаётся alert, drift metrics сохраняются в БД, а active model получает `retrain_required=True`. Также создаётся retraining event. Полный training pipeline можно подключить позже через worker/CI/CD/job scheduler.

**Что бы ты улучшил дальше?**

Object storage для reports/baselines, async worker queue для тяжёлых reports, auth/RBAC для alert lifecycle, model registry для promotion workflows, Pandera/Great Expectations для richer validation, real deployment with persistent managed Postgres.

## Что показывать в коде

- `app/services/ingestion_service.py`: orchestration ingestion pipeline.
- `app/services/model_service.py`: loading model artifact and fallback scorer.
- `app/services/drift_service.py`: drift persistence and retraining hook.
- `app/monitoring/drift_calculator.py`: PSI implementation.
- `app/services/alert_service.py`: alert lifecycle logic.
- `app/services/baseline_service.py`: baseline versioning.
- `app/dashboard/templates/dashboard.html`: interview-facing UI.
- `alembic/versions/`: database schema evolution.
- `.github/workflows/ci.yml`: CI checks.

## Финальный pitch

Коротко можно сказать так:

> Это не просто модель за API. Это маленький production-like monitoring layer для credit scoring: сервис принимает batch, валидирует данные, делает predictions через сохранённый sklearn artifact, сохраняет prediction logs, сравнивает features с versioned baseline, генерирует Evidently report, пишет drift/performance metrics в PostgreSQL, создаёт alerts и retraining events, а dashboard показывает историю и текущее состояние системы.
