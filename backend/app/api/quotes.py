from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import Quote
from app.schemas import QuoteOut

router = APIRouter()


@router.get("/quotes")
def list_quotes(response: Response, db: Session = Depends(get_db)):
    cache_headers(response, 60)
    rows = db.scalars(select(Quote).order_by(Quote.grp, Quote.symbol)).all()
    return {
        "updated_at": datetime.now(timezone.utc),
        "items": [QuoteOut.model_validate(r) for r in rows],
    }
