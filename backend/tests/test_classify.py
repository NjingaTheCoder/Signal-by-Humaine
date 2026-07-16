from app.classify import classify_rules


def test_source_prior_applied():
    cats = classify_rules("Some headline with no keywords", None, "Retail Dive")
    assert "retail" in cats


def test_ai_martech_keyword():
    cats = classify_rules("New generative AI tool for marketers", "Built on GPT-4", "Digiday")
    assert "ai-martech" in cats


def test_agency_keyword_account_win():
    cats = classify_rules("WPP wins account move for major retailer", None, "Digiday")
    assert "agency" in cats


def test_search_media_keyword():
    cats = classify_rules("Google Ads rolls out new PPC bidding feature", None, "Digiday")
    assert "search-media" in cats


def test_b2b_keyword():
    cats = classify_rules("HubSpot launches new ABM demand gen tool", None, "MarTech")
    assert "b2b" in cats


def test_no_match_returns_empty():
    cats = classify_rules("A completely unrelated headline about weather", None, "Unknown Source")
    assert cats == []


def test_multiple_categories_can_apply():
    cats = classify_rules(
        "Retail media platform launches generative AI ad tool", "CDP and CRM integration included", "Retail Dive"
    )
    assert "retail" in cats
    assert "ai-martech" in cats


def test_aeo_keyword_maps_to_search_media():
    cats = classify_rules("Brands race to win AEO as answer engine visibility grows", None, "Digiday")
    assert "search-media" in cats


def test_agentic_ai_keyword():
    cats = classify_rules("Startup launches agentic AI-native workflow for marketers", None, "Digiday")
    assert "ai-martech" in cats


def test_saas_gtm_keyword_maps_to_b2b():
    cats = classify_rules("SaaS company overhauls its GTM motion", None, "Digiday")
    assert "b2b" in cats
