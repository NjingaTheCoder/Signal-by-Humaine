def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["db"] == "ok"
    assert "last_runs" in body


def test_news_empty(client):
    resp = client.get("/api/news")
    assert resp.status_code == 200
    body = resp.json()
    assert "updated_at" in body
    assert body["items"] == []


def test_funding_empty(client):
    resp = client.get("/api/funding?window=30")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stats"]["disclosed_round_count"] == 0
    assert body["rounds"] == []


def test_tenders_empty(client):
    resp = client.get("/api/tenders?type=all")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []


def test_quotes_empty(client):
    resp = client.get("/api/quotes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []


def test_briefing_latest_none(client):
    resp = client.get("/api/briefing/latest")
    assert resp.status_code == 200
    assert resp.json()["briefing"] is None


def test_jobs_empty(client):
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_resources_empty(client):
    resp = client.get("/api/resources")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_subscribe_valid_email(client):
    resp = client.post("/api/subscribe", json={"email": "reviewer@example.com"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_subscribe_invalid_email(client):
    resp = client.post("/api/subscribe", json={"email": "not-an-email"})
    assert resp.status_code == 422


def test_admin_requires_auth(client):
    resp = client.get("/admin/")
    assert resp.status_code == 401
