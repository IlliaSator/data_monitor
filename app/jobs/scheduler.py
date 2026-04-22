from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs.periodic_jobs import reconcile_retrain_flags, refresh_monitoring_snapshot


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_monitoring_snapshot,
        trigger="interval",
        minutes=5,
        id="refresh_monitoring_snapshot",
        replace_existing=True,
    )
    scheduler.add_job(
        reconcile_retrain_flags,
        trigger="interval",
        minutes=10,
        id="reconcile_retrain_flags",
        replace_existing=True,
    )
    return scheduler
