# Signal by Humaine

Live marketing-industry intelligence terminal for [Humaine](https://wearehumaine.com). FastAPI backend
ingests real news, funding, tender, stock and blog data on a schedule into Postgres; React serves it up
through six live panels. One Railway service, no CORS, no fake data — see `../CLAUDE.md`-style brief for
the full spec this was built against.

## Local development

Prerequisites: Python 3.12+, Node 20+, a local Postgres (or a disposable Docker container).

```bash
# 1. Database
docker run -d --name signal-pg -e POSTGRES_USER=signal -e POSTGRES_PASSWORD=signal \
  -e POSTGRES_DB=signal -p 5432:5432 postgres:16-alpine

# 2. Backend
cd backend
python -m venv .venv
./.venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp ../.env.example .env   # copied INTO backend/, since config.py resolves .env relative to CWD
                          # fill in DATABASE_URL at minimum
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd web
npm install
npm run fetch-fonts   # downloads self-hosted Objektiv fonts from wearehumaine.com
npm run dev           # proxies /api to localhost:8000
```

The app boots with only `DATABASE_URL` set — jobs needing a missing key (Finnhub, Anthropic, HubSpot)
log a skip message and no-op rather than crashing.

Every ingestion module supports a `--once` CLI flag for manual runs and verification:

```bash
python -m app.ingest.news --once
python -m app.ingest.quotes --once
python -m app.ingest.funding --once
python -m app.ingest.tenders --once --window yesterday
python -m app.ingest.blog --once
```

Run the test suite (needs a reachable Postgres; defaults to a `signal_test` database on
localhost:5432 — override with `DATABASE_URL` if your local Postgres runs on a different port,
e.g. because another project already holds 5432):

```bash
cd backend
pytest tests -q
```

## Environment variables

See `.env.example`. Only `DATABASE_URL` is required to boot. Everything else gates an optional feature:

| Var | Gates |
|---|---|
| `FINNHUB_API_KEY` | Stock quotes (Markets panel stays empty without it) |
| `ANTHROPIC_API_KEY` | LLM classification cleanup + funding headline fallback parsing (regex-only without it) |
| `ADMIN_USER` / `ADMIN_PASSWORD` | `/admin` HTTP Basic auth |
| `HUBSPOT_ACCESS_TOKEN` | Subscriber push to HubSpot CRM |

## Adding a news feed

1. Add an entry to `NEWS_SOURCES` in `backend/app/ingest/news.py`: `source` (display name), `url`
   (direct RSS URL), `domain` (bare domain for the Google News fallback).
2. If the publisher is known to block scrapers (Cloudflare, aggressive rate limiting), set
   `force_google: True` to skip straight to the Google News RSS mirror.
3. Run `python -m app.ingest.news --once` and check `source_health` for the fetch mode that
   succeeded (`direct` or `googlenews`) and any error.
4. Add a source prior to `SOURCE_PRIORS` in `backend/app/classify.py` if the outlet reliably belongs
   to one category (e.g. a retail trade title always gets `retail`).

## Admin usage

`/admin` (HTTP Basic, `ADMIN_USER` / `ADMIN_PASSWORD`):

- **Briefings** — list drafts, edit the five text fields + benchmark pair, save or publish.
- **Jobs board** — add/deactivate roles shown in Careers & Collabs.
- **Health** — last 20 job runs (ok/fail/rows) and per-source fetch health.
- **Subscribers** — count + CSV export.

## The Monday briefing runbook

1. `briefing_draftpack` runs Mondays 05:00 UTC (07:00 SAST) and creates a `draft` briefing from the
   past week's top articles, funding rounds, and large tenders.
2. An editor reviews and edits the draft in `/admin/briefings` by **08:45 SAST**.
3. Publish by **09:00 SAST** — this sets `status=published`, `published_at=now()`, and makes it live
   at `GET /api/briefing/latest`.
4. The draft pack never auto-publishes; a human always reviews first.

## Rotating a key

Update the variable in Railway's environment settings and redeploy (or restart) — nothing is cached
outside `pydantic-settings`' process-lifetime `lru_cache`, so a redeploy is sufficient.

## Notes on data quality

- Funding currency conversion uses coarse fixed rates (EUR 1.1, GBP 1.3, ZAR 0.055) — the Funding
  panel is directional, not accounting.
- Tenders are filtered by CPV code family (79 3xx / 79800 / 79960) OR a marketing keyword match,
  because buyers misclassify CPV codes; expect some false positives in the raw feed.
- All timestamps are stored and scheduled in UTC; the UI displays SAST (UTC+2).
