from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import JobRun
from app.schemas import HealthOut

router = APIRouter()

JOB_NAMES = [
    "ingest_news",
    "ingest_quotes",
    "ingest_tenders_uk",
    "ingest_tenders_intl",
    "ingest_funding",
    "ingest_blog",
    "ingest_jobs",
    "classify_batch",
    "briefing_draftpack",
]


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    db_status = "ok"
    try:
        db.execute(select(1))
    except Exception:  # noqa: BLE001
        db_status = "error"

    last_runs: dict[str, datetime | None] = {}
    for job in JOB_NAMES:
        row = db.scalar(
            select(JobRun).where(JobRun.job == job, JobRun.ok.is_(True)).order_by(JobRun.finished.desc())
        )
        last_runs[job] = row.finished if row else None

    return HealthOut(db=db_status, last_runs=last_runs)
