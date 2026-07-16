"""Finnhub stock quotes (§5.4). No yfinance/Yahoo per project rules."""
import argparse
import logging
import time
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.db import SessionLocal
from app.models import Quote

logger = logging.getLogger("signal.ingest.quotes")

HOLDCOS = [("WPP", "WPP plc"), ("OMC", "Omnicom"), ("IPG", "Interpublic Group"), ("STGW", "Stagwell")]
PLATFORMS = [
    ("HUBS", "HubSpot"),
    ("CRM", "Salesforce"),
    ("ADBE", "Adobe"),
    ("SHOP", "Shopify"),
    ("TTD", "The Trade Desk"),
    ("APP", "AppLovin"),
    ("BRZE", "Braze"),
    ("KVYO", "Klaviyo"),
    ("META", "Meta Platforms"),
    ("GOOGL", "Alphabet"),
]
AI_COMPANIES = [
    ("NVDA", "Nvidia"),
    ("MSFT", "Microsoft"),
    ("PLTR", "Palantir"),
    ("AI", "C3.ai"),
    ("PATH", "UiPath"),
    ("SOUN", "SoundHound AI"),
]
PROBE_ONLY = [("PUBGY", "Publicis Groupe (ADR)")]

FINNHUB_URL = "https://finnhub.io/api/v1/quote"


def _fetch_one(client: httpx.Client, symbol: str, token: str) -> dict | None:
    resp = client.get(FINNHUB_URL, params={"symbol": symbol, "token": token}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data or data.get("c") in (None, 0):
        return None
    return data


def ingest_quotes() -> int:
    settings = get_settings()
    if not settings.finnhub_api_key:
        logger.info("ingest_quotes skipped: no FINNHUB_API_KEY set")
        return 0

    db = SessionLocal()
    written = 0
    try:
        with httpx.Client() as client:
            symbols = (
                [(s, n, "holdco") for s, n in HOLDCOS]
                + [(s, n, "platform") for s, n in PLATFORMS]
                + [(s, n, "ai") for s, n in AI_COMPANIES]
            )

            # probe optional symbols once; include if they return real data
            for symbol, name in PROBE_ONLY:
                data = _fetch_one(client, symbol, settings.finnhub_api_key)
                time.sleep(0.2)
                if data:
                    symbols.append((symbol, name, "holdco"))
                else:
                    logger.info("probe symbol %s returned no data; omitting", symbol)

            for symbol, name, grp in symbols:
                try:
                    data = _fetch_one(client, symbol, settings.finnhub_api_key)
                except Exception:  # noqa: BLE001
                    logger.exception("finnhub fetch failed for %s; keeping stale price", symbol)
                    data = None
                time.sleep(0.2)

                if data is None:
                    continue  # keep previous stored price (stale-but-honest)

                quote = db.get(Quote, symbol)
                if quote is None:
                    quote = Quote(symbol=symbol, name=name, grp=grp)
                    db.add(quote)
                quote.name = name
                quote.grp = grp
                quote.price = data["c"]
                quote.change_pct = data.get("dp")
                quote.quoted_at = datetime.now(timezone.utc)
                written += 1
            db.commit()
    finally:
        db.close()
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    n = ingest_quotes()
    print(f"ingest_quotes wrote {n} quotes")
