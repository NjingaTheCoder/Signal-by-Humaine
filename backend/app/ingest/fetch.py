"""Shared fetch layer with a three-step fallback chain (direct -> browser UA -> Google News mirror).

Per source_health, tracks which fetch mode last succeeded so repeatedly-blocked
sources skip straight to the Google News mirror and only re-probe direct weekly.
"""
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlparse

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.models import SourceHealth

logger = logging.getLogger("signal.ingest.fetch")

DIRECT_UA = "HumaineSignal/1.0 (+https://signal.wearehumaine.com; RSS reader)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DIRECT_FAILURE_THRESHOLD = 5
DIRECT_REPROBE_INTERVAL = timedelta(days=7)


@dataclass
class FetchResult:
    entries: list[dict] = field(default_factory=list)
    mode: str = "direct"  # direct | googlenews
    ok: bool = False
    error: str | None = None


def _is_challenge_page(status: int, body: bytes) -> bool:
    if status in (403, 429):
        return True
    head = body[:200].lstrip()
    return head.startswith(b"<!DOCTYPE html") and b"Just a moment" in body[:2000]


def _get_health(db: Session, source: str) -> SourceHealth:
    health = db.get(SourceHealth, source)
    if health is None:
        health = SourceHealth(source=source, fetch_mode="direct", consecutive_failures=0)
        db.add(health)
        db.flush()
    return health


def _google_news_url(domain: str, query_extra: str = "") -> str:
    q = f"site:{domain}{query_extra} when:2d"
    return f"https://news.google.com/rss/search?q={quote(q)}&hl=en-GB&gl=GB&ceid=GB:en"


# Google News formats titles as "{headline} - {Source}". Matching on the trailing
# "-{non-dash text}" with flexible surrounding whitespace (rather than a literal " - ")
# handles a real edge case: when Google has no real headline for an item, the raw title
# is just " - {Source}", and feedparser normalizes away the leading space before this
# runs, leaving "- {Source}" — a literal " - " match silently misses that and leaves the
# dash-prefixed source name stored as a fake headline. This resolves both cases to the
# same (correctly empty, for the no-headline case) result.
_GOOGLE_SUFFIX_RE = re.compile(r"\s*-\s*[^-]+$")


def _strip_google_suffix(title: str) -> str:
    return _GOOGLE_SUFFIX_RE.sub("", title, count=1).strip()


def _parse_feed_bytes(content: bytes) -> list[dict]:
    parsed = feedparser.parse(content)
    return [dict(e) for e in parsed.entries]


def fetch_direct(client: httpx.Client, url: str, etag: str | None, last_modified: str | None) -> tuple[int, bytes, str | None, str | None]:
    headers = {"User-Agent": DIRECT_UA}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    resp = client.get(url, headers=headers, timeout=15, follow_redirects=True)
    return resp.status_code, resp.content, resp.headers.get("ETag"), resp.headers.get("Last-Modified")


def fetch_browser_ua(client: httpx.Client, url: str) -> tuple[int, bytes]:
    resp = client.get(url, headers={"User-Agent": BROWSER_UA}, timeout=15, follow_redirects=True)
    return resp.status_code, resp.content


def fetch_google_news(client: httpx.Client, domain: str, query_extra: str = "") -> list[dict]:
    gurl = _google_news_url(domain, query_extra)
    resp = client.get(gurl, headers={"User-Agent": BROWSER_UA}, timeout=15)
    resp.raise_for_status()
    entries = _parse_feed_bytes(resp.content)
    out = []
    for e in entries:
        title = _strip_google_suffix(e.get("title", ""))
        out.append({**e, "title": title})
    return out


def fetch_source(
    db: Session,
    client: httpx.Client,
    source: str,
    direct_url: str,
    domain: str,
    google_query_extra: str = "",
    force_google: bool = False,
) -> FetchResult:
    """Runs the fallback chain for one source and updates source_health."""
    health = _get_health(db, source)
    now = datetime.now(timezone.utc)

    should_try_direct = not force_google and (
        health.fetch_mode == "direct"
        or health.consecutive_failures < DIRECT_FAILURE_THRESHOLD
        or (health.last_ok and now - health.last_ok > DIRECT_REPROBE_INTERVAL)
        or health.last_ok is None
    )

    if should_try_direct:
        try:
            status, body, etag, last_mod = fetch_direct(client, direct_url, None, None)
            if status == 304:
                health.last_ok = now
                health.consecutive_failures = 0
                health.fetch_mode = "direct"
                return FetchResult(entries=[], mode="direct", ok=True)
            if not _is_challenge_page(status, body) and status == 200:
                entries = _parse_feed_bytes(body)
                health.last_ok = now
                health.consecutive_failures = 0
                health.fetch_mode = "direct"
                health.last_error = None
                return FetchResult(entries=entries, mode="direct", ok=True)

            # step 2: browser UA retry
            status2, body2 = fetch_browser_ua(client, direct_url)
            if status2 == 200 and not _is_challenge_page(status2, body2):
                entries = _parse_feed_bytes(body2)
                health.last_ok = now
                health.consecutive_failures = 0
                health.fetch_mode = "direct"
                health.last_error = None
                return FetchResult(entries=entries, mode="direct", ok=True)

            raise RuntimeError(f"direct+browserUA failed status={status}/{status2}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("direct fetch failed for %s: %s", source, exc)
            health.consecutive_failures += 1
            health.last_error = str(exc)

    # step 3: Google News mirror
    try:
        entries = fetch_google_news(client, domain, google_query_extra)
        health.fetch_mode = "googlenews" if health.consecutive_failures >= DIRECT_FAILURE_THRESHOLD else health.fetch_mode
        health.last_ok = now
        health.last_error = None
        return FetchResult(entries=entries, mode="googlenews", ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.error("google news fallback failed for %s: %s", source, exc)
        health.last_error = str(exc)
        return FetchResult(entries=[], mode="googlenews", ok=False, error=str(exc))


def polite_sleep(seconds: float = 0.2) -> None:
    time.sleep(seconds)


def domain_of(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")
