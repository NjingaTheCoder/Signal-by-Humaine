from app.ingest.jobs import _clean, _extract_type, _is_relevant


def test_relevant_marketing_title():
    assert _is_relevant("Social Media Manager")
    assert _is_relevant("Chief Growth Officer")
    assert _is_relevant("Junior Content Writer")
    assert _is_relevant("Head of Brand Operations")
    assert _is_relevant("Product Manager AI")


def test_irrelevant_title():
    assert not _is_relevant("Backend Engineer")
    assert not _is_relevant("Warehouse Associate")
    assert not _is_relevant("Servpro is Hiring")


def test_relevant_ai_specific_titles():
    # AI/ML engineering, product, and leadership roles signal a company building real
    # AI capability — Humaine's ideal customer profile.
    assert _is_relevant("Senior AI Engineer Architect")
    assert _is_relevant("Head of AI")
    assert _is_relevant("Director of AI Strategy")
    assert _is_relevant("AI Product Manager")
    assert _is_relevant("Member of Technical Staff Applied ML RecSys")
    assert _is_relevant("Generative AI Lead")
    assert _is_relevant("Data Scientist")


def test_irrelevant_ai_adjacent_title_not_swept_in():
    # Loose "ai" substring shouldn't false-positive on unrelated words.
    assert not _is_relevant("Maintenance Technician")
    assert not _is_relevant("Retail Sales Associate")


def test_clean_drops_mojibake_control_characters():
    # Real-world case: RemoteOK occasionally serves location strings with mixed/corrupted
    # encoding (raw C1 control bytes mixed into otherwise-valid Arabic text). Rather than
    # display garbage or guess a "correction", treat the field as unusable.
    corrupted = "دب\x8a, دب\x8a ا\x84إ\x85ارات"
    assert _clean(corrupted, max_len=80) == ""


def test_clean_normal_unicode_text_unaffected():
    assert _clean("Cape Town, South Africa") == "Cape Town, South Africa"


def test_extract_type_matches_known_tag():
    assert _extract_type(["design", "full time", "remote"]) == "full time"
    assert _extract_type(["contract", "senior"]) == "contract"


def test_extract_type_returns_none_when_no_match():
    assert _extract_type(["design", "senior", "remote"]) is None


def test_clean_unescapes_html_entities():
    assert _clean("Head of Creative Studio &amp; Brand Operations") == "Head of Creative Studio & Brand Operations"


def test_clean_strips_html_tags():
    assert _clean("<strong>Senior</strong> Marketer") == "Senior Marketer"


def test_clean_strips_trailing_comma_from_empty_location_part():
    assert _clean("Los Angeles, ") == "Los Angeles"


def test_clean_truncates_to_max_len():
    long_location = "Comunidad Valenciana / Comunitat Valenciana, Comunidad Valenciana / Comunitat Valenciana, España"
    result = _clean(long_location, max_len=80)
    assert len(result) <= 80
    assert result.endswith("…")


def test_clean_leaves_short_text_under_max_len_unchanged():
    assert _clean("Cape Town", max_len=80) == "Cape Town"
