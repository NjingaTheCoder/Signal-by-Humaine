from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import Article, Tender
from app.schemas import ArticleOut, TenderOut

router = APIRouter()


@router.get("/tenders")
def list_tenders(
    response: Response,
    type: str = Query(default="all", pattern="^(all|tender|win)$"),
    db: Session = Depends(get_db),
):
    cache_headers(response, 300)
    items: list[dict] = []

    if type in ("all", "tender"):
        rows = db.scalars(select(Tender).order_by(Tender.published_at.desc()).limit(100)).all()
        items.extend(TenderOut.model_validate(r).model_dump() for r in rows)

    if type in ("all", "win"):
        wins = db.scalars(
            select(Article).where(Article.is_win.is_(True)).order_by(Article.published_at.desc()).limit(50)
        ).all()
        for a in wins:
            items.append(
                {
                    "id": a.id,
                    "ocid": f"win-{a.id}",
                    "title": a.title,
                    "description": a.snippet,
                    "buyer": None,
                    "value_amount": None,
                    "value_currency": None,
                    "cpv_codes": None,
                    "region": "WIN",
                    "stage": "win",
                    "deadline": None,
                    "source_url": a.url,
                    "published_at": a.published_at,
                    "is_win": True,
                }
            )

    items.sort(key=lambda i: i["published_at"], reverse=True)
    return {"updated_at": datetime.now(timezone.utc), "items": items}
