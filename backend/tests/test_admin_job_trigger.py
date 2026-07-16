from unittest.mock import patch

from sqlalchemy import select

from app.models import JobRun


def _auth():
    import base64

    creds = base64.b64encode(b"signal-admin:testpass").decode()
    return {"Authorization": f"Basic {creds}"}


def test_health_page_lists_triggerable_jobs(client, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")
    from app.config import get_settings

    get_settings.cache_clear()
    resp = client.get("/admin/health", headers=_auth())
    assert resp.status_code == 200
    assert "ingest_news" in resp.text
    assert "briefing_draftpack" in resp.text


def test_run_unknown_job_returns_404(client, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")
    from app.config import get_settings

    get_settings.cache_clear()
    resp = client.post("/admin/health/run/not_a_real_job", headers=_auth())
    assert resp.status_code == 404


def test_run_known_job_triggers_and_writes_job_run(client, db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")
    from app.config import get_settings

    get_settings.cache_clear()
    with patch("app.ingest.blog.ingest_blog", return_value=3) as mock_blog:
        resp = client.post("/admin/health/run/ingest_blog", headers=_auth())
        assert resp.status_code == 200  # TestClient follows the redirect by default
        assert "triggered=ingest_blog" in str(resp.url)
        mock_blog.assert_called_once()

    run = db_session.scalar(select(JobRun).where(JobRun.job == "ingest_blog"))
    assert run is not None
    assert run.ok is True
    assert run.rows_written == 3
