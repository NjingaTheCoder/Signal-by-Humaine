from app.ingest.fetch import _strip_google_suffix


def test_strips_normal_headline_and_source():
    title = "Why agentic commerce will matter more than ChatGPT ads - Search Engine Land"
    assert _strip_google_suffix(title) == "Why agentic commerce will matter more than ChatGPT ads"


def test_preserves_internal_dash_in_headline():
    title = "Google Ads - New Feature - Search Engine Land"
    assert _strip_google_suffix(title) == "Google Ads - New Feature"


def test_empty_headline_with_leading_space_resolves_to_empty():
    # Raw Google News title is " - Search Engine Land" (no real headline available);
    # feedparser normalizes away the leading space before this runs.
    title = "- Search Engine Land"
    assert _strip_google_suffix(title) == ""


def test_empty_headline_with_space_preserved_resolves_to_empty():
    title = " - Search Engine Land"
    assert _strip_google_suffix(title) == ""


def test_title_without_source_suffix_is_unchanged():
    assert _strip_google_suffix("A headline with no suffix") == "A headline with no suffix"
