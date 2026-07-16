"""UK tenders ingestion via Contracts Finder + Find a Tender OCDS APIs (§5.3)."""
import argparse
import logging
import re
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Tender

logger = logging.getLogger("signal.ingest.tenders")

CONTRACTS_FINDER_URL = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"
FIND_A_TENDER_URL = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"

CPV_PREFIXES = ("793", "79800", "79960")
KEYWORD_RE = re.compile(
    r"\b(marketing|advertis\w*|campaign|creative|brand(ing)?|content|CRM|social media|"
    r"digital agency|media buying|email marketing)\b",
    re.I,
)


def _is_relevant(title: str, description: str, cpv_codes: list[str]) -> bool:
    if any(any(cpv.startswith(p) for p in CPV_PREFIXES) for cpv in cpv_codes):
        return True
    return bool(KEYWORD_RE.search(f"{title} {description or ''}"))


def _extract_source_url(release: dict, region: str) -> str | None:
    tender = release.get("tender") or {}
    if region == "UK":
        # Contracts Finder releases carry a human-readable notice link in tender.documents.
        for doc in tender.get("documents") or []:
            url = doc.get("url", "")
            if "contractsfinder.service.gov.uk" in url:
                return url
        return None
    if region == "UK-FTS":
        # Find a Tender has no documents[] in the OCDS payload, but notice pages follow a
        # predictable pattern keyed on the release id (e.g. "039768-2025").
        release_id = release.get("id")
        return f"https://www.find-tender.service.gov.uk/Notice/{release_id}" if release_id else None
    return None


def _extract_cpv_codes(tender: dict) -> list[str]:
    codes = []
    classification = tender.get("classification") or {}
    if classification.get("id"):
        codes.append(str(classification["id"]))
    for item in tender.get("items", []) or []:
        cls = item.get("classification") or {}
        if cls.get("id"):
            codes.append(str(cls["id"]))
    return codes


def _parse_release(release: dict, region: str) -> Tender | None:
    ocid = release.get("ocid")
    tender = release.get("tender") or {}
    if not ocid or not tender:
        return None

    title = tender.get("title") or "(untitled)"
    description = tender.get("description")
    cpv_codes = _extract_cpv_codes(tender)
    if not _is_relevant(title, description or "", cpv_codes):
        return None

    buyer = (release.get("buyer") or {}).get("name")
    value = tender.get("value") or {}
    deadline_raw = (tender.get("tenderPeriod") or {}).get("endDate")
    deadline = None
    if deadline_raw:
        try:
            deadline = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))
        except ValueError:
            deadline = None

    date_raw = release.get("date")
    try:
        published_at = datetime.fromisoformat(date_raw.replace("Z", "+00:00")) if date_raw else datetime.now(timezone.utc)
    except ValueError:
        published_at = datetime.now(timezone.utc)

    return Tender(
        ocid=ocid,
        title=title,
        description=description,
        buyer=buyer,
        value_amount=value.get("amount"),
        value_currency=value.get("currency"),
        cpv_codes=cpv_codes or None,
        region=region,
        stage=tender.get("status", "tender"),
        deadline=deadline,
        source_url=_extract_source_url(release, region),
        published_at=published_at,
    )


def _upsert(db, tender: Tender) -> bool:
    existing = db.scalar(select(Tender).where(Tender.ocid == tender.ocid))
    if existing:
        return False
    db.add(tender)
    return True


def _fetch_with_backoff(client: httpx.Client, url: str, params: dict, max_retries: int = 3) -> dict | None:
    delay = 2.0
    for attempt in range(max_retries):
        try:
            resp = client.get(url, params=params, timeout=30)
            if resp.status_code == 403:
                logger.warning("403 (rate limit) from %s, backing off %.1fs", url, delay)
                time.sleep(delay)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("tender fetch attempt %d failed: %s", attempt + 1, exc)
            time.sleep(delay)
            delay *= 2
    return None


def ingest_tenders_uk(window: str = "yesterday") -> int:
    db = SessionLocal()
    written = 0
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    published_from = f"{yesterday}T00:00:00"
    published_to = f"{today}T00:00:00"

    try:
        with httpx.Client() as client:
            data = _fetch_with_backoff(
                client,
                CONTRACTS_FINDER_URL,
                {"publishedFrom": published_from, "publishedTo": published_to, "stages": "tender"},
            )
            if data:
                for release in data.get("releases", []):
                    t = _parse_release(release, "UK")
                    if t and _upsert(db, t):
                        written += 1
                db.commit()

            data2 = _fetch_with_backoff(
                client,
                FIND_A_TENDER_URL,
                {"updatedFrom": published_from, "updatedTo": published_to, "limit": 100},
            )
            if data2:
                for release in data2.get("releases", []):
                    t = _parse_release(release, "UK-FTS")
                    if t and _upsert(db, t):
                        written += 1
                db.commit()
    finally:
        db.close()
    return written


def ingest_tenders_intl() -> int:
    """EU (TED) / SA (eTenders) — phase-4 addition, not blocking launch. Logs a TODO."""
    logger.info("ingest_tenders_intl: TED/SA eTenders not yet wired; UK-only for now")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--window", default="yesterday")
    args = parser.parse_args()
    n = ingest_tenders_uk(window=args.window)
    print(f"ingest_tenders_uk wrote {n} tenders")
