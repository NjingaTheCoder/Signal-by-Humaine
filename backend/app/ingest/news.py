"""News ingestion (§5.1) and Monday briefing draft pack (§5.6)."""
import argparse
import hashlib
import logging
import re
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import bleach
import httpx
from sqlalchemy import select

from app.classify import classify_rules
from app.db import SessionLocal
from app.ingest.fetch import domain_of, fetch_source, polite_sleep
from app.models import Article, Briefing, FundingRound, Tender

logger = logging.getLogger("signal.ingest.news")

NEWS_SOURCES: list[dict] = [
    {"source": "Digiday", "url": "https://digiday.com/feed/", "domain": "digiday.com"},
    {"source": "MarTech", "url": "https://martech.org/feed/", "domain": "martech.org"},
    {"source": "Marketing Dive", "url": "https://www.marketingdive.com/feeds/news/", "domain": "marketingdive.com"},
    {"source": "Retail Dive", "url": "https://www.retaildive.com/feeds/news/", "domain": "retaildive.com"},
    {"source": "chiefmartec", "url": "https://chiefmartec.com/feed/", "domain": "chiefmartec.com"},
    {
        "source": "Search Engine Journal",
        "url": "https://www.searchenginejournal.com/feed/",
        "domain": "searchenginejournal.com",
    },
    {"source": "Sifted", "url": "https://sifted.eu/feed", "domain": "sifted.eu"},
    {
        "source": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "domain": "techcrunch.com",
    },
    {
        "source": "Search Engine Land",
        "url": "https://searchengineland.com/feed/",
        "domain": "searchengineland.com",
    },
    {"source": "Marketing Week", "url": "https://www.marketingweek.com/feed/", "domain": "marketingweek.com"},
    {"source": "Retail Gazette", "url": "https://www.retailgazette.co.uk/feed/", "domain": "retailgazette.co.uk"},
    {
        "source": "The Drum",
        "url": "https://www.thedrum.com/rss.xml",
        "domain": "thedrum.com",
        "force_google": True,
    },
    {
        "source": "Bizcommunity Marketing SA",
        "url": "https://www.bizcommunity.com/",
        "domain": "bizcommunity.com",
        "force_google": True,
        "google_query_extra": " marketing",
    },
]

WIN_PATTERN = re.compile(
    r"\b(wins|appoints|picks|selects|hands|retains)\b.*\b(account|AOR|agency|creative|media|CRM|brief)\b", re.I
)

_STRIP_PARAMS = re.compile(r"^utm_")


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(parts.query) if not _STRIP_PARAMS.match(k)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def normalise_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())


def strip_html(text: str) -> str:
    return bleach.clean(text or "", tags=[], strip=True).strip()


def make_snippet(entry: dict) -> str:
    raw = entry.get("summary") or entry.get("description") or ""
    text = strip_html(raw)
    return text[:300]


def parse_published(entry: dict) -> datetime:
    for key in ("published", "updated"):
        val = entry.get(key)
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (TypeError, ValueError):
                continue
    return datetime.now(timezone.utc)


def ingest_news(window_hours: int = 48) -> int:
    db = SessionLocal()
    written = 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    recent_titles: set[str] = {
        normalise_title(t)
        for (t,) in db.execute(
            select(Article.title).where(Article.published_at >= cutoff)
        ).all()
    }
    try:
        with httpx.Client() as client:
            for src in NEWS_SOURCES:
                result = fetch_source(
                    db,
                    client,
                    source=src["source"],
                    direct_url=src["url"],
                    domain=src["domain"],
                    google_query_extra=src.get("google_query_extra", ""),
                    force_google=src.get("force_google", False),
                )
                db.commit()
                if not result.ok:
                    continue
                for entry in result.entries:
                    title = (entry.get("title") or "").strip()
                    link = entry.get("link") or ""
                    if not title or not link:
                        continue
                    norm_title = normalise_title(title)
                    if result.mode == "googlenews":
                        if norm_title in recent_titles:
                            continue
                        canon_url = link  # redirect URLs kept as-is per spec
                        uhash = url_hash(canon_url)
                    else:
                        canon_url = canonicalize_url(link)
                        uhash = url_hash(canon_url)

                    existing = db.scalar(select(Article).where(Article.url_hash == uhash))
                    if existing:
                        continue
                    if norm_title in recent_titles:
                        continue

                    snippet = make_snippet(entry)
                    published_at = parse_published(entry)
                    categories = classify_rules(title, snippet, src["source"])
                    is_win = bool(WIN_PATTERN.search(title))

                    article = Article(
                        url_hash=uhash,
                        url=canon_url,
                        title=title,
                        source=src["source"],
                        snippet=snippet or None,
                        published_at=published_at,
                        categories=categories,
                        is_win=is_win,
                        classified=1 <= len(categories) <= 3,
                    )
                    db.add(article)
                    recent_titles.add(norm_title)
                    written += 1
                db.commit()
                polite_sleep()
    finally:
        db.close()
    return written


def briefing_draftpack() -> int:
    """Assembles the Monday briefing draft pack (§5.6). Never auto-publishes."""
    db = SessionLocal()
    try:
        since = datetime.now(timezone.utc) - timedelta(days=7)
        articles = db.scalars(
            select(Article).where(Article.published_at >= since).order_by(Article.published_at.desc()).limit(15)
        ).all()
        funding_rows = db.scalars(
            select(FundingRound).where(FundingRound.announced_at >= since)
        ).all()
        tenders = db.scalars(
            select(Tender)
            .where(Tender.published_at >= since, Tender.value_amount > 250000)
        ).all()

        # Bullets use markdown-style [text](url) links so the frontend can render them as
        # clickable references back to the real source, and so an admin hand-editing the
        # draft in the textarea can add/keep links using the same simple syntax.
        moved_lines = [f"- [{a.title}]({a.url}) ({a.source})" for a in articles[:3]]
        tape_lines = [
            f"- [{f.company}: {f.round or 'undisclosed round'}]({f.source_url})" for f in funding_rows[:5]
        ]
        next_lines = []
        for t in tenders[:3]:
            bullet = f"[{t.title}]({t.source_url})" if t.source_url else t.title
            if t.buyer:
                bullet += f" ({t.buyer})"
            next_lines.append(f"- {bullet}")

        last = db.scalar(select(Briefing).order_by(Briefing.number.desc()))
        number = (last.number + 1) if last else 1

        briefing = Briefing(
            number=number,
            week_of=date.today(),
            headline="DRAFT — edit before publishing",
            section_moved="\n".join(moved_lines) or "No items this week.",
            section_tape="\n".join(tape_lines) or "No funding rounds this week.",
            section_next="\n".join(next_lines) or "No large tenders this week.",
            benchmark_value=None,
            benchmark_label=None,
            status="draft",
        )
        db.add(briefing)
        db.commit()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    n = ingest_news()
    print(f"ingest_news wrote {n} articles")
