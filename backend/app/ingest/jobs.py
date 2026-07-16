"""Industry job listings for Careers & Collabs.

Pulls real, live listings from RemoteOK's public API (no auth required) and keeps
only ones that look like marketing/growth/content/brand/creative roles, or AI-specific
roles (AI/ML engineering, product, and leadership) — companies hiring for the latter
are exactly Humaine's ideal customer profile: organizations actively building AI
capability. Industry-wide (any real company), not exclusively Humaine's own openings,
which stay admin-curated via /admin/jobs-board (source IS NULL) and are never touched
here.

Fetches both the default feed and the "ai" tag feed and merges+dedupes by job id —
RemoteOK's tags= query param doesn't filter server-side (it just returns a different
recent slice), but combining both roughly doubles real coverage.

Per RemoteOK's API terms of service: "Please link back... and mention Remote OK as a
source" — see the attribution line rendered in the Careers & Collabs panel.
"""
import argparse
import html
import logging
import re

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.ingest.fetch import DIRECT_UA
from app.models import JobPosting

logger = logging.getLogger("signal.ingest.jobs")

REMOTEOK_URL = "https://remoteok.com/api"
REMOTEOK_AI_TAG_URL = "https://remoteok.com/api?tags=ai"
SOURCE_NAME = "RemoteOK"

TITLE_RELEVANCE_RE = re.compile(
    r"market|growth|content|brand|\bseo\b|\bsem\b|social media|copywrit|advertis|"
    r"paid (search|media|social)|agency|creative director|community manager|"
    # AI-specific: engineering/product/leadership roles signal a company building real
    # AI capability, not just any mention of "ai" in an unrelated tag list.
    r"\bai\b|artificial intelligence|machine learning|\bml\b|generative ai|applied ai|"
    r"applied ml|ai (engineer|product|lead|architect|strategist|researcher)|"
    r"(head|director|vp|chief) of ai|chief ai officer|ai transformation|data scien",
    re.I,
)

TYPE_TAGS = ("full time", "part time", "contract", "freelance", "internship")


# C1 control characters (U+0080-U+009F) never appear in legitimate text; seeing one is a
# reliable signal of source-side mojibake (RemoteOK occasionally serves fields with mixed,
# corrupted encoding — e.g. Arabic location names with stray raw bytes). Rather than guess
# at a "correction" and risk showing wrong text, treat the field as unusable.
_MOJIBAKE_RE = re.compile("[\x80-\x9f]")


def _clean(text: str, max_len: int | None = None) -> str:
    if _MOJIBAKE_RE.search(text or ""):
        return ""
    cleaned = html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()
    cleaned = re.sub(r"\s*,\s*$", "", cleaned)  # trailing ", " left by empty location parts
    if max_len and len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 1].rstrip() + "…"
    return cleaned


def _extract_type(tags: list[str]) -> str | None:
    lowered = {t.lower() for t in tags}
    for t in TYPE_TAGS:
        if t in lowered:
            return t
    return None


def _is_relevant(position: str) -> bool:
    return bool(TITLE_RELEVANCE_RE.search(position or ""))


def _fetch_entries(client: httpx.Client, url: str) -> list[dict]:
    resp = client.get(url, headers={"User-Agent": DIRECT_UA}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [e for e in data if isinstance(e, dict) and "position" in e]


def ingest_jobs() -> int:
    db = SessionLocal()
    written = 0

    by_id: dict[str, dict] = {}
    with httpx.Client() as client:
        for url in (REMOTEOK_URL, REMOTEOK_AI_TAG_URL):
            try:
                for entry in _fetch_entries(client, url):
                    by_id[entry.get("id") or entry.get("apply_url") or entry.get("url")] = entry
            except Exception:  # noqa: BLE001
                logger.exception("RemoteOK fetch failed for %s", url)
    entries = list(by_id.values())

    if not entries:
        logger.warning("RemoteOK fetch returned no entries")
        db.close()
        return 0

    try:
        seen_urls: set[str] = set()
        for entry in entries:
            raw_position = entry.get("position")
            apply_url = entry.get("apply_url") or entry.get("url")
            if not raw_position or not apply_url or not _is_relevant(raw_position):
                continue

            position = _clean(raw_position)
            company = _clean(entry.get("company") or "", max_len=40) or None
            location = _clean(entry.get("location") or "", max_len=80) or None
            job_type = _extract_type(entry.get("tags") or [])

            seen_urls.add(apply_url)
            existing = db.scalar(
                select(JobPosting).where(
                    JobPosting.apply_url == apply_url, JobPosting.source == SOURCE_NAME
                )
            )

            if existing:
                existing.role = position
                existing.lab = company
                existing.location = location
                existing.type = job_type
                existing.active = True
            else:
                db.add(
                    JobPosting(
                        role=position,
                        lab=company,
                        location=location,
                        type=job_type,
                        apply_url=apply_url,
                        active=True,
                        source=SOURCE_NAME,
                    )
                )
                written += 1

        # Delist (not delete) previously-ingested roles no longer present in this fetch —
        # never touches admin-curated rows (source IS NULL).
        stale = db.scalars(
            select(JobPosting).where(JobPosting.source == SOURCE_NAME, JobPosting.active.is_(True))
        ).all()
        for job in stale:
            if job.apply_url not in seen_urls:
                job.active = False

        db.commit()
    finally:
        db.close()
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    n = ingest_jobs()
    print(f"ingest_jobs wrote {n} new jobs")
