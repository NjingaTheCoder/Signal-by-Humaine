from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import Briefing
from app.schemas import BriefingOut

router = APIRouter()


@router.get("/briefing/latest")
def latest_briefing(response: Response, db: Session = Depends(get_db)):
    cache_headers(response, 300)
    row = db.scalar(
        select(Briefing).where(Briefing.status == "published").order_by(Briefing.published_at.desc())
    )
    if row is None:
        return {"briefing": None}
    return {"briefing": BriefingOut.model_validate(row)}
