from app.ingest.funding import guess_category, parse_headline


def test_guess_category_ai_agents():
    assert guess_category("New agentic AI agent platform for sales teams") == "ai-agents"


def test_guess_category_answer_engine():
    assert guess_category("Startup raises funding for answer engine optimization") == "ai-search"


def test_guess_category_martech_still_works():
    assert guess_category("New martech CDP integration announced") == "martech"


def test_guess_category_no_match_returns_none():
    assert guess_category("A completely unrelated headline about weather") is None


def test_parse_headline_extracts_amount_and_round():
    parsed = parse_headline("Acme raises $12M in Series A funding")
    assert parsed is not None
    assert parsed["amount_usd"] == 12_000_000
    assert parsed["round"] == "Series A"
