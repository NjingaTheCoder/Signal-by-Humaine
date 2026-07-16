from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import JobPosting
from app.schemas import JobOut

router = APIRouter()


@router.get("/jobs")
def list_jobs(response: Response, db: Session = Depends(get_db)):
    cache_headers(response, 300)
    rows = db.scalars(
        select(JobPosting).where(JobPosting.active.is_(True)).order_by(JobPosting.created_at.desc())
    ).all()
    return {
        "updated_at": datetime.now(timezone.utc),
        "items": [JobOut.model_validate(r) for r in rows],
    }
