from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import cache_headers
from app.db import get_db
from app.models import FundingRound
from app.schemas import FundingResponse, FundingRoundOut, FundingStats

router = APIRouter()


def _window_start(window: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if window == "7":
        return now - timedelta(days=7)
    if window == "30":
        return now - timedelta(days=30)
    if window == "ytd":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc)
    # "all" (or any other value): no lower bound.
    return None


@router.get("/funding", response_model=FundingResponse)
def list_funding(
    response: Response,
    window: str = Query(default="30", pattern="^(7|30|ytd|all)$"),
    db: Session = Depends(get_db),
) -> FundingResponse:
    cache_headers(response, 300)
    start = _window_start(window)
    stmt = select(FundingRound).order_by(FundingRound.announced_at.desc())
    if start:
        stmt = stmt.where(FundingRound.announced_at >= start)
    rows = db.scalars(stmt).all()

    disclosed = [r for r in rows if r.amount_usd is not None]
    excluding_megadeals = [r for r in disclosed if r.amount_usd <= 500_000_000]
    capital_deployed = sum(float(r.amount_usd) for r in disclosed)
    avg_deal = (
        sum(float(r.amount_usd) for r in excluding_megadeals) / len(excluding_megadeals)
        if excluding_megadeals
        else None
    )
    by_category_value = Counter()
    for r in disclosed:
        if r.category:
            by_category_value[r.category] += float(r.amount_usd)
    top_category = by_category_value.most_common(1)[0][0] if by_category_value else None

    stats = FundingStats(
        window=window,
        capital_deployed_usd=capital_deployed,
        disclosed_round_count=len(disclosed),
        avg_deal_usd=avg_deal,
        top_category=top_category,
    )

    return FundingResponse(
        updated_at=datetime.now(timezone.utc),
        stats=stats,
        rounds=[FundingRoundOut.model_validate(r) for r in rows],
    )
