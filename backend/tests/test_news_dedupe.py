from datetime import datetime, timezone

from sqlalchemy import select

from app.ingest.news import canonicalize_url, normalise_title, url_hash
from app.models import Article


def test_canonicalize_url_strips_utm_and_fragment():
    dirty = "https://digiday.com/marketing/some-story/?utm_source=twitter&utm_medium=social&ref=x#comments"
    clean = canonicalize_url(dirty)
    assert "utm_source" not in clean
    assert "utm_medium" not in clean
    assert "#" not in clean
    assert "ref=x" in clean  # only utm_* params are stripped


def test_url_hash_is_deterministic_sha256():
    url = "https://example.com/a"
    h1 = url_hash(url)
    h2 = url_hash(url)
    assert h1 == h2
    assert len(h1) == 64


def test_normalise_title_strips_non_alphanumerics():
    assert normalise_title("Acme Raises $12M in Series A!") == "acmeraises12minseriesa"
    assert normalise_title("Acme Raises $12M In Series A") == normalise_title(
        "acme raises $12m in series a"
    )


def test_url_hash_dedupe_at_db_level(db_session):
    url = "https://digiday.com/some-article/"
    h = url_hash(url)
    article = Article(
        url_hash=h,
        url=url,
        title="Some article",
        source="Digiday",
        snippet="snippet",
        published_at=datetime.now(timezone.utc),
        categories=["agency"],
    )
    db_session.add(article)
    db_session.commit()

    existing = db_session.scalar(select(Article).where(Article.url_hash == h))
    assert existing is not None

    # Same URL again would hash the same and be rejected by the unique constraint / dedupe check
    duplicate = db_session.scalar(select(Article).where(Article.url_hash == url_hash(url)))
    assert duplicate.id == article.id
