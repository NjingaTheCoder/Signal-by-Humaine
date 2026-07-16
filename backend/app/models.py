from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Date,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    snippet: Mapped[str | None] = mapped_column(String(400))
    published_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    categories: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    is_win: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    classified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class FundingRound(Base):
    __tablename__ = "funding_rounds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    amount_usd: Mapped[float | None] = mapped_column(Numeric(14, 0))
    round: Mapped[str | None] = mapped_column(String(40))
    category: Mapped[str | None] = mapped_column(String(60))
    investors: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    announced_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    parse_method: Mapped[str] = mapped_column(String(10), nullable=False)


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ocid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    buyer: Mapped[str | None] = mapped_column(Text)
    value_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    value_currency: Mapped[str | None] = mapped_column(String(3))
    cpv_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    source_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class Quote(Base):
    __tablename__ = "quotes"

    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    grp: Mapped[str] = mapped_column(String(12), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    change_pct: Mapped[float | None] = mapped_column(Numeric(8, 3))
    quoted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class Briefing(Base):
    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_of: Mapped[date] = mapped_column(Date, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    section_moved: Mapped[str] = mapped_column(Text, nullable=False)
    section_tape: Mapped[str] = mapped_column(Text, nullable=False)
    section_next: Mapped[str] = mapped_column(Text, nullable=False)
    benchmark_value: Mapped[str | None] = mapped_column(String(24))
    benchmark_label: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class JobPosting(Base):
    __tablename__ = "jobs_board"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    lab: Mapped[str | None] = mapped_column(String(40))
    location: Mapped[str | None] = mapped_column(String(80))
    type: Mapped[str | None] = mapped_column(String(20))
    apply_url: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    # NULL = admin-curated Humaine role; a source name (e.g. "RemoteOK") = ingested
    # industry listing. Lets ingestion safely deactivate only rows it owns.
    source: Mapped[str | None] = mapped_column(String(40))


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(400))
    published_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    hubspot_synced: Mapped[bool] = mapped_column(Boolean, server_default="false")


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job: Mapped[str] = mapped_column(String(40), nullable=False)
    started: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    finished: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    rows_written: Mapped[int] = mapped_column(Integer, server_default="0")
    ok: Mapped[bool | None] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(Text)


class SourceHealth(Base):
    __tablename__ = "source_health"

    source: Mapped[str] = mapped_column(String(80), primary_key=True)
    last_ok: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, server_default="0")
    fetch_mode: Mapped[str] = mapped_column(String(12), server_default="direct")
