from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import Article
from app.schemas import ArticleOut

router = APIRouter()

VALID_CATEGORIES = {"ai-martech", "b2b", "retail", "agency", "search-media"}


@router.get("/news")
def list_news(
    response: Response,
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=60, le=200),
    db: Session = Depends(get_db),
):
    cache_headers(response, 300)
    stmt = select(Article).order_by(Article.published_at.desc())
    if category and category != "all" and category in VALID_CATEGORIES:
        stmt = stmt.where(Article.categories.any(category))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Article.title.ilike(like))
    stmt = stmt.limit(limit)
    rows = db.scalars(stmt).all()
    return {
        "updated_at": datetime.now(timezone.utc),
        "items": [ArticleOut.model_validate(r) for r in rows],
    }
