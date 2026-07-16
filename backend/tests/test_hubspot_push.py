import httpx
import pytest

from app.api.subscribe import push_to_hubspot


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text or "{}"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)


@pytest.fixture(autouse=True)
def _set_token(monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "fake-token")
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_no_token_returns_false_without_any_request(monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "")
    from app.config import get_settings

    get_settings.cache_clear()
    assert push_to_hubspot("a@example.com") is False


def test_success_on_first_attempt(monkeypatch):
    calls = []

    def fake_create(email, properties, token):
        calls.append(properties)
        return _FakeResponse(201)

    monkeypatch.setattr("app.api.subscribe._create_hubspot_contact", fake_create)
    assert push_to_hubspot("a@example.com") is True
    assert len(calls) == 1
    assert "signal_source" in calls[0]


def test_409_conflict_treated_as_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.subscribe._create_hubspot_contact",
        lambda email, properties, token: _FakeResponse(409),
    )
    assert push_to_hubspot("a@example.com") is True


def test_400_retries_with_email_only_and_succeeds(monkeypatch):
    calls = []

    def fake_create(email, properties, token):
        calls.append(properties)
        if len(calls) == 1:
            return _FakeResponse(400, text='{"message":"Property \\"signal_source\\" does not exist"}')
        return _FakeResponse(201)

    monkeypatch.setattr("app.api.subscribe._create_hubspot_contact", fake_create)
    assert push_to_hubspot("a@example.com") is True
    assert len(calls) == 2
    assert calls[0] == {
        "email": "a@example.com",
        "lifecyclestage": "lead",
        "hs_lead_status": "NEW",
        "signal_source": "signal_terminal",
    }
    assert calls[1] == {"email": "a@example.com"}


def test_400_retry_also_fails_returns_false(monkeypatch):
    monkeypatch.setattr(
        "app.api.subscribe._create_hubspot_contact",
        lambda email, properties, token: _FakeResponse(400, text="still broken"),
    )
    assert push_to_hubspot("a@example.com") is False


def test_other_error_status_returns_false(monkeypatch):
    monkeypatch.setattr(
        "app.api.subscribe._create_hubspot_contact",
        lambda email, properties, token: _FakeResponse(401, text="invalid token"),
    )
    assert push_to_hubspot("a@example.com") is False
