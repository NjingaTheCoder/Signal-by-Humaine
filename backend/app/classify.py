"""Article classification: fast inline rules (stage 1) + optional LLM batch (stage 2)."""
import json
import logging
import re

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Article

logger = logging.getLogger("signal.classify")

CATEGORY_SLUGS = ["ai-martech", "b2b", "retail", "agency", "search-media"]

SOURCE_PRIORS: dict[str, list[str]] = {
    "Retail Dive": ["retail"],
    "Retail Gazette": ["retail"],
    "Search Engine Journal": ["search-media"],
    "Search Engine Land": ["search-media"],
    "Digiday": ["agency"],
    "The Drum": ["agency"],
    "MarTech": ["ai-martech"],
    "chiefmartec": ["ai-martech"],
}

KEYWORD_RULES: dict[str, re.Pattern] = {
    # AI-native workflows and tooling — Humaine's Tech + IP / Strategy Lab territory, not just
    # "martech" broadly. Includes agentic/AI-native workflow language Humaine uses about itself.
    "ai-martech": re.compile(
        r"\b(AI|LLM|GPT|generative|agentic|AI[- ]native|AI workflow|automation|martech|CDP|"
        r"Claude|Gemini|OpenAI|Anthropic|AI agent|AI assistant|AI readiness)\b",
        re.I,
    ),
    # B2B/SaaS GTM — Humaine's B2B client base is specifically technology/SaaS, and "GTM" is
    # their own term for this work (Strategic Growth and GTM Modernisation).
    "b2b": re.compile(
        r"\b(B2B|ABM|demand gen|pipeline|lead gen|HubSpot|Salesforce|CRM|SaaS|go-to-market|GTM)\b",
        re.I,
    ),
    "retail": re.compile(r"\b(retail|ecommerce|e-commerce|DTC|grocer|high street|retail media|shopper)\b", re.I),
    "agency": re.compile(
        r"\b(agency|pitch|AOR|holdco|WPP|Publicis|Omnicom|IPG|Stagwell|account (win|move))\b", re.I
    ),
    # Search & AI discovery — classic SEO/SEM plus AEO (answer engine optimization) and the AI
    # discovery surfaces (AI Overviews, ChatGPT/Perplexity search) that are Humaine's Search Lab
    # focus: "AI assistants, marketplaces and discovery platforms increasingly shape how people
    # find and choose brands."
    "search-media": re.compile(
        r"\b(SEO|SEM|AEO|GEO|answer engine|search ads|PPC|Google Ads|Meta Ads|programmatic|CTV|"
        r"AI Overviews?|AI search|generative engine|ChatGPT search|Perplexity)\b",
        re.I,
    ),
}


def classify_rules(title: str, snippet: str | None, source: str) -> list[str]:
    cats: set[str] = set(SOURCE_PRIORS.get(source, []))
    text = f"{title} {snippet or ''}"
    for slug, pattern in KEYWORD_RULES.items():
        if pattern.search(text):
            cats.add(slug)
    return sorted(cats)


def classify_batch(limit: int = 150) -> int:
    """Stage 2: LLM cleanup for rows with 0 or >3 categories. No-op without an API key."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.info("classify_batch skipped: no ANTHROPIC_API_KEY set")
        return 0

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    db = SessionLocal()
    written = 0
    try:
        rows = db.scalars(
            select(Article)
            .where(Article.classified.is_(False))
            .limit(limit)
        ).all()
        for row in rows:
            if 1 <= len(row.categories) <= 3:
                row.classified = True
                continue
            try:
                msg = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=200,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Classify this marketing-industry news headline for Signal, an "
                                "intelligence terminal read by Humaine, an AI-native growth agency "
                                "serving B2B SaaS and retail clients. Assign 1-3 of these "
                                f"categories: {CATEGORY_SLUGS}. Respond with JSON only: "
                                '{"categories": ["slug", ...]}.\n\n'
                                f"Title: {row.title}\nSnippet: {row.snippet or ''}"
                            ),
                        }
                    ],
                )
                text = msg.content[0].text
                data = json.loads(text)
                cats = [c for c in data.get("categories", []) if c in CATEGORY_SLUGS]
                row.categories = cats
            except Exception:  # noqa: BLE001
                logger.exception("classify_batch failed for article %s", row.id)
            row.classified = True
            written += 1
        db.commit()
    finally:
        db.close()
    return written
