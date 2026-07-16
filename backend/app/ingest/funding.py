"""Funding rounds ingestion (§5.2)."""
import argparse
import html
import json
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.ingest.fetch import BROWSER_UA, DIRECT_UA, fetch_source, polite_sleep
from app.models import FundingRound

logger = logging.getLogger("signal.ingest.funding")

FX_TO_USD = {"$": 1.0, "€": 1.1, "£": 1.3, "R": 0.055}
MAGNITUDE = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "million": 1_000_000, "billion": 1_000_000_000}

SECTOR_LEXICON = re.compile(
    r"\b(martech|adtech|CRM|CDP|retail media|e-?commerce tech|creative AI|content automation|"
    r"measurement|analytics|agency M&A|marketing|AI agents?|agentic|answer engine|AEO|GEO)\b",
    re.I,
)

FUNDING_REGEX = re.compile(
    r"(?P<company>.+?)\s+(raises|raised|secures|closes|lands|nets)\s+"
    r"(?P<cur>[$€£R])(?P<num>[\d.,]+)\s?(?P<mag>[MBK]|million|billion)\b",
    re.I,
)

# Matched separately against the full headline: embedding this inside FUNDING_REGEX as a trailing
# optional group after a lazy `.*?` never actually matches, since the engine is satisfied as soon
# as the (optional) round group matches zero characters.
ROUND_REGEX = re.compile(r"\b(pre-?seed|seed|series [a-f]|growth|debt|bridge)\b", re.I)

CATEGORY_MAP = {
    "martech": "martech",
    "adtech": "adtech",
    "crm": "data-crm",
    "cdp": "data-crm",
    "retail media": "retail-tech",
    "ecommerce tech": "retail-tech",
    "e-commerce tech": "retail-tech",
    "creative ai": "creative-ai",
    "content automation": "creative-ai",
    "measurement": "analytics",
    "analytics": "analytics",
    "agency m&a": "agency-ma",
    "ai agent": "ai-agents",
    "ai agents": "ai-agents",
    "agentic": "ai-agents",
    "answer engine": "ai-search",
    "aeo": "ai-search",
    "geo": "ai-search",
}


def _strip_google_suffix(title: str) -> str:
    for suffix in (" - FinSMEs",):
        if title.endswith(suffix):
            return title[: -len(suffix)]
    return title


def guess_category(text: str) -> str | None:
    m = SECTOR_LEXICON.search(text)
    if not m:
        return None
    return CATEGORY_MAP.get(m.group(1).lower(), "martech")


def parse_headline(headline: str) -> dict | None:
    m = FUNDING_REGEX.search(headline)
    if not m:
        return None
    cur = m.group("cur")
    num = float(m.group("num").replace(",", ""))
    mag = m.group("mag").lower()
    multiplier = MAGNITUDE.get(mag, 1)
    amount_native = num * multiplier
    amount_usd = amount_native * FX_TO_USD.get(cur, 1.0)
    round_match = ROUND_REGEX.search(headline)
    return {
        "company": m.group("company").strip(" -–"),
        "amount_usd": round(amount_usd),
        "round": round_match.group(1).title() if round_match else None,
    }


def _classify_and_maybe_llm(headline: str, excerpt: str, client=None) -> dict | None:
    text = f"{headline} {excerpt}"
    parsed = parse_headline(headline)
    category = guess_category(text)

    if parsed is not None:
        if category is None:
            return None  # not in sector lexicon; discard
        return {**parsed, "category": category, "parse_method": "regex"}

    settings = get_settings()
    if not settings.anthropic_api_key:
        return None  # regex-only mode: discard unparsed

    import anthropic

    ai_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        msg = ai_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract a funding round from this headline/excerpt if it is relevant to "
                        "Signal, an intelligence terminal read by Humaine, an AI-native growth agency "
                        "serving B2B SaaS and retail clients. Relevant sectors: marketing tech, adtech, "
                        "CRM, CDP, retail media, e-commerce tech, creative AI, content automation, "
                        "AI agents/agentic tooling, answer engine optimization (AEO/GEO), "
                        "measurement/analytics, or agency M&A. Respond with JSON only: "
                        '{"company": str, "amount_usd": number|null, "round": str|null, '
                        '"category": str|null, "relevant": bool}.\n\n'
                        f"Headline: {headline}\nExcerpt: {excerpt}"
                    ),
                }
            ],
        )
        data = json.loads(msg.content[0].text)
        if not data.get("relevant"):
            return None
        return {
            "company": data.get("company") or headline,
            "amount_usd": data.get("amount_usd"),
            "round": data.get("round"),
            "category": data.get("category") or "martech",
            "parse_method": "llm",
        }
    except Exception:  # noqa: BLE001
        logger.exception("LLM funding parse failed for headline: %s", headline)
        return None


def ingest_funding() -> int:
    db = SessionLocal()
    written = 0
    try:
        with httpx.Client() as client:
            written += _ingest_techcrunch(db, client)
            written += _ingest_crunchbase(db, client)
            written += _ingest_finsmes(db, client)
            db.commit()
    finally:
        db.close()
    return written


def _upsert(db, source_url: str, company: str, amount_usd, round_, category, announced_at, source, parse_method) -> bool:
    existing = db.scalar(select(FundingRound).where(FundingRound.source_url == source_url))
    if existing:
        return False
    db.add(
        FundingRound(
            source_url=source_url,
            company=company[:255],
            amount_usd=amount_usd,
            round=round_,
            category=category,
            investors=None,
            announced_at=announced_at,
            source=source,
            parse_method=parse_method,
        )
    )
    return True


def _ingest_techcrunch(db, client: httpx.Client) -> int:
    result = fetch_source(
        db, client, source="TechCrunch Funding",
        direct_url="https://techcrunch.com/tag/funding/feed/", domain="techcrunch.com",
    )
    db.commit()
    written = 0
    if not result.ok:
        return 0
    for entry in result.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        excerpt = entry.get("summary", "")
        if not title or not link:
            continue
        parsed = _classify_and_maybe_llm(title, excerpt)
        if parsed is None:
            continue
        try:
            announced = parsedate_to_datetime(entry.get("published")) if entry.get("published") else datetime.now(timezone.utc)
            if announced.tzinfo is None:
                announced = announced.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            announced = datetime.now(timezone.utc)
        if _upsert(db, link, parsed["company"], parsed.get("amount_usd"), parsed.get("round"),
                   parsed["category"], announced, "TechCrunch", parsed["parse_method"]):
            written += 1
    db.commit()
    polite_sleep()
    return written


def _ingest_crunchbase(db, client: httpx.Client) -> int:
    written = 0
    try:
        resp = client.get(
            "https://news.crunchbase.com/wp-json/wp/v2/posts",
            params={"per_page": 20, "_fields": "title,link,date,excerpt"},
            headers={"User-Agent": DIRECT_UA},
            timeout=15,
        )
        if resp.status_code in (403, 429):
            resp = client.get(
                "https://news.crunchbase.com/wp-json/wp/v2/posts",
                params={"per_page": 20, "_fields": "title,link,date,excerpt"},
                headers={"User-Agent": BROWSER_UA},
                timeout=15,
            )
        resp.raise_for_status()
        posts = resp.json()
    except Exception:  # noqa: BLE001
        logger.exception("crunchbase news fetch failed")
        return 0

    for post in posts:
        title = html.unescape(post.get("title", {}).get("rendered", ""))
        link = post.get("link", "")
        excerpt = html.unescape(re.sub(r"<[^>]+>", "", post.get("excerpt", {}).get("rendered", "")))
        if not title or not link:
            continue
        parsed = _classify_and_maybe_llm(title, excerpt)
        if parsed is None:
            continue
        try:
            announced = datetime.fromisoformat(post["date"]).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            announced = datetime.now(timezone.utc)
        if _upsert(db, link, parsed["company"], parsed.get("amount_usd"), parsed.get("round"),
                   parsed["category"], announced, "Crunchbase News", parsed["parse_method"]):
            written += 1
    db.commit()
    return written


def _ingest_finsmes(db, client: httpx.Client) -> int:
    result = fetch_source(
        db, client, source="FinSMEs",
        direct_url="https://www.finsmes.com/feed", domain="finsmes.com",
        force_google=True,
    )
    db.commit()
    written = 0
    if not result.ok:
        return 0
    for entry in result.entries:
        title = _strip_google_suffix(entry.get("title", ""))
        link = entry.get("link", "")
        excerpt = entry.get("summary", "")
        if not title or not link:
            continue
        parsed = _classify_and_maybe_llm(title, excerpt)
        if parsed is None:
            continue
        announced = datetime.now(timezone.utc)
        if _upsert(db, link, parsed["company"], parsed.get("amount_usd"), parsed.get("round"),
                   parsed["category"], announced, "FinSMEs", parsed["parse_method"]):
            written += 1
    db.commit()
    polite_sleep()
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    n = ingest_funding()
    print(f"ingest_funding wrote {n} rounds")
