from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import Resource
from app.schemas import ResourceOut

router = APIRouter()


@router.get("/resources")
def list_resources(response: Response, db: Session = Depends(get_db)):
    cache_headers(response, 300)
    rows = db.scalars(select(Resource).order_by(Resource.published_at.desc()).limit(9)).all()
    return {
        "updated_at": datetime.now(timezone.utc),
        "items": [ResourceOut.model_validate(r) for r in rows],
    }
