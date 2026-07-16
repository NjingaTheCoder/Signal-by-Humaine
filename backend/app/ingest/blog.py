"""Humaine blog ingestion (§5.5)."""
import argparse
import html
import logging
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.ingest.fetch import DIRECT_UA
from app.models import Resource

logger = logging.getLogger("signal.ingest.blog")

BLOG_URL = "https://wearehumaine.com/wp-json/wp/v2/posts"


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def ingest_blog() -> int:
    db = SessionLocal()
    written = 0
    try:
        with httpx.Client() as client:
            resp = client.get(
                BLOG_URL,
                params={"per_page": 9, "_fields": "title,link,date,excerpt"},
                headers={"User-Agent": DIRECT_UA},
                timeout=15,
            )
            resp.raise_for_status()
            posts = resp.json()
    except Exception:  # noqa: BLE001
        logger.exception("humaine blog fetch failed")
        db.close()
        return 0

    try:
        for post in posts:
            link = post.get("link")
            if not link:
                continue
            title = html.unescape(post.get("title", {}).get("rendered", ""))
            excerpt = _strip_html(post.get("excerpt", {}).get("rendered", ""))[:400]
            try:
                published_at = datetime.fromisoformat(post["date"]).replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                published_at = datetime.now(timezone.utc)

            existing = db.scalar(select(Resource).where(Resource.url == link))
            if existing:
                existing.title = title
                existing.excerpt = excerpt
                continue
            db.add(Resource(url=link, title=title, excerpt=excerpt, published_at=published_at))
            written += 1
        db.commit()
    finally:
        db.close()
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    n = ingest_blog()
    print(f"ingest_blog wrote {n} resources")
