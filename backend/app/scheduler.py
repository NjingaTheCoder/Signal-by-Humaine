import functools
import logging
from collections.abc import Callable
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import SessionLocal
from app.models import JobRun

logger = logging.getLogger("signal.scheduler")

scheduler = BackgroundScheduler(timezone="UTC")


def tracked_job(name: str) -> Callable:
    """Wraps a job so every run is recorded in job_runs and no exception
    escapes to kill the scheduler thread."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            started = datetime.now(timezone.utc)
            db = SessionLocal()
            run = JobRun(job=name, started=started)
            db.add(run)
            db.commit()
            db.refresh(run)

            rows_written = 0
            error = None
            ok = False
            try:
                result = fn(*args, **kwargs)
                if isinstance(result, int):
                    rows_written = result
                ok = True
            except Exception as exc:  # noqa: BLE001 - job must never crash the process
                logger.exception("job %s failed", name)
                ok = False
                error = str(exc)
            finally:
                run.finished = datetime.now(timezone.utc)
                run.ok = ok
                run.rows_written = rows_written
                run.error = error
                db.add(run)
                db.commit()
                db.close()
            return rows_written

        return wrapper

    return decorator


def register_jobs() -> None:
    """Registers all recurring ingestion jobs. Imported lazily to avoid
    circular imports and so `--once` CLI invocations don't start the
    scheduler."""
    from app.ingest import blog, funding, jobs, news, quotes, tenders
    from app.classify import classify_batch

    scheduler.add_job(
        news.ingest_news,
        "cron",
        minute=5,
        id="ingest_news",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        quotes.ingest_quotes,
        "cron",
        day_of_week="mon-fri",
        minute="0,15,30,45",
        hour="13-20",
        id="ingest_quotes",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        tenders.ingest_tenders_uk,
        "cron",
        hour=5,
        minute=0,
        id="ingest_tenders_uk",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        tenders.ingest_tenders_intl,
        "cron",
        day_of_week="mon",
        hour=5,
        minute=30,
        id="ingest_tenders_intl",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        jobs.ingest_jobs,
        "cron",
        hour=7,
        minute=30,
        id="ingest_jobs",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        funding.ingest_funding,
        "cron",
        hour=4,
        minute=0,
        id="ingest_funding",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        blog.ingest_blog,
        "cron",
        hour=6,
        minute=0,
        id="ingest_blog",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        classify_batch,
        "cron",
        hour=3,
        minute=30,
        id="classify_batch",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    from app.ingest.news import briefing_draftpack

    scheduler.add_job(
        briefing_draftpack,
        "cron",
        day_of_week="mon",
        hour=5,
        minute=0,
        id="briefing_draftpack",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
