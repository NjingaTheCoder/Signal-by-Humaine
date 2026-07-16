from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    updated_at: datetime
    items: T


class ArticleOut(BaseModel):
    id: int
    url: str
    title: str
    source: str
    snippet: str | None
    published_at: datetime
    categories: list[str]
    is_win: bool

    model_config = ConfigDict(from_attributes=True)


class FundingRoundOut(BaseModel):
    id: int
    company: str
    amount_usd: float | None
    round: str | None
    category: str | None
    investors: list[str] | None
    announced_at: datetime
    source: str
    source_url: str

    model_config = ConfigDict(from_attributes=True)


class FundingStats(BaseModel):
    window: str
    capital_deployed_usd: float
    disclosed_round_count: int
    avg_deal_usd: float | None
    top_category: str | None


class FundingResponse(BaseModel):
    updated_at: datetime
    stats: FundingStats
    rounds: list[FundingRoundOut]


class TenderOut(BaseModel):
    id: int
    ocid: str
    title: str
    description: str | None
    buyer: str | None
    value_amount: float | None
    value_currency: str | None
    cpv_codes: list[str] | None
    region: str
    stage: str
    deadline: datetime | None
    source_url: str | None
    published_at: datetime
    is_win: bool = False

    model_config = ConfigDict(from_attributes=True)


class QuoteOut(BaseModel):
    symbol: str
    name: str
    grp: str
    price: float | None
    change_pct: float | None
    quoted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BriefingOut(BaseModel):
    id: int
    number: int
    week_of: date
    headline: str
    section_moved: str
    section_tape: str
    section_next: str
    benchmark_value: str | None
    benchmark_label: str | None
    status: str
    published_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class JobOut(BaseModel):
    id: int
    role: str
    lab: str | None
    location: str | None
    type: str | None
    apply_url: str | None

    model_config = ConfigDict(from_attributes=True)


class ResourceOut(BaseModel):
    id: int
    url: str
    title: str
    excerpt: str | None
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscribeIn(BaseModel):
    email: EmailStr


class SubscribeOut(BaseModel):
    ok: bool


class HealthOut(BaseModel):
    db: str
    last_runs: dict[str, datetime | None]
