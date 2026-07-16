import json
from pathlib import Path

from app.ingest.tenders import _extract_cpv_codes, _extract_source_url, _is_relevant, _parse_release

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "ocds_sample.json").read_text())


def _release(ocid: str) -> dict:
    return next(r for r in FIXTURE["releases"] if r["ocid"] == ocid)


def test_cpv_prefix_match_marks_relevant():
    release = _release("ocds-test-0001")
    cpv_codes = _extract_cpv_codes(release["tender"])
    assert "79341400" in cpv_codes
    assert "79341000" in cpv_codes
    assert "72000000" in cpv_codes
    assert _is_relevant(release["tender"]["title"], release["tender"]["description"], cpv_codes)


def test_irrelevant_tender_is_filtered_out():
    release = _release("ocds-0002" if False else "ocds-test-0002")
    cpv_codes = _extract_cpv_codes(release["tender"])
    assert cpv_codes == ["39130000"]
    assert not _is_relevant(release["tender"]["title"], release["tender"]["description"], cpv_codes)


def test_keyword_net_catches_misclassified_cpv():
    release = _release("ocds-test-0003")
    cpv_codes = _extract_cpv_codes(release["tender"])
    assert cpv_codes == []
    assert _is_relevant(release["tender"]["title"], "", cpv_codes)


def test_parse_release_populates_fields_for_relevant_tender():
    release = _release("ocds-test-0001")
    tender = _parse_release(release, "UK")
    assert tender is not None
    assert tender.ocid == "ocds-test-0001"
    assert tender.buyer == "Test Council"
    assert float(tender.value_amount) == 150000
    assert tender.value_currency == "GBP"
    assert tender.region == "UK"
    assert tender.deadline is not None
    assert tender.source_url == "https://www.contractsfinder.service.gov.uk/Notice/56fbe42c-0e0c-47d2-aeb5-b51505b8cd86"


def test_extract_source_url_contracts_finder_prefers_own_domain():
    release = _release("ocds-test-0001")
    url = _extract_source_url(release, "UK")
    assert url == "https://www.contractsfinder.service.gov.uk/Notice/56fbe42c-0e0c-47d2-aeb5-b51505b8cd86"
    assert "mytenders.co.uk" not in url


def test_extract_source_url_find_a_tender_uses_release_id():
    release = _release("ocds-test-0005")
    url = _extract_source_url(release, "UK-FTS")
    assert url == "https://www.find-tender.service.gov.uk/Notice/039768-2025"


def test_parse_release_uk_fts_populates_source_url():
    release = _release("ocds-test-0005")
    tender = _parse_release(release, "UK-FTS")
    assert tender is not None
    assert tender.source_url == "https://www.find-tender.service.gov.uk/Notice/039768-2025"


def test_extract_source_url_missing_documents_returns_none():
    release = _release("ocds-test-0002")
    assert _extract_source_url(release, "UK") is None


def test_parse_release_returns_none_for_irrelevant_tender():
    release = _release("ocds-test-0002")
    assert _parse_release(release, "UK") is None


def test_parse_release_tolerates_missing_value_and_deadline():
    release = _release("ocds-test-0003")
    tender = _parse_release(release, "UK-FTS")
    assert tender is not None
    assert tender.value_amount is None
    assert tender.deadline is None
    assert tender.stage == "planning"


def test_parse_release_tolerates_empty_tender_and_missing_date():
    release = _release("ocds-test-0004")
    assert _parse_release(release, "UK") is None
