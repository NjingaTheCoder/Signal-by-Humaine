import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin.auth import require_admin
from app.db import get_db
from app.models import Briefing, JobPosting, JobRun, SourceHealth, Subscriber

router = APIRouter(dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="app/admin/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {})


@router.get("/briefings", response_class=HTMLResponse)
def briefings_list(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(Briefing).order_by(Briefing.number.desc())).all()
    return templates.TemplateResponse(request, "briefings.html", {"briefings": rows})


@router.get("/briefings/{briefing_id}", response_class=HTMLResponse)
def briefing_edit(request: Request, briefing_id: int, db: Session = Depends(get_db)):
    row = db.get(Briefing, briefing_id)
    return templates.TemplateResponse(request, "briefing_edit.html", {"b": row})


@router.post("/briefings/{briefing_id}")
def briefing_save(
    briefing_id: int,
    headline: str = Form(...),
    section_moved: str = Form(...),
    section_tape: str = Form(...),
    section_next: str = Form(...),
    benchmark_value: str = Form(""),
    benchmark_label: str = Form(""),
    publish: str = Form(""),
    db: Session = Depends(get_db),
):
    row = db.get(Briefing, briefing_id)
    row.headline = headline
    row.section_moved = section_moved
    row.section_tape = section_tape
    row.section_next = section_next
    row.benchmark_value = benchmark_value or None
    row.benchmark_label = benchmark_label or None
    if publish == "1":
        row.status = "published"
        row.published_at = datetime.now(timezone.utc)
    db.commit()
    return RedirectResponse(url="/admin/briefings", status_code=303)


@router.get("/jobs-board", response_class=HTMLResponse)
def jobs_board_list(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(select(JobPosting).order_by(JobPosting.created_at.desc())).all()
    return templates.TemplateResponse(request, "jobs_board.html", {"jobs": rows})


@router.post("/jobs-board")
def jobs_board_create(
    role: str = Form(...),
    lab: str = Form(""),
    location: str = Form(""),
    type: str = Form(""),
    apply_url: str = Form(""),
    db: Session = Depends(get_db),
):
    db.add(JobPosting(role=role, lab=lab or None, location=location or None, type=type or None, apply_url=apply_url or None))
    db.commit()
    return RedirectResponse(url="/admin/jobs-board", status_code=303)


@router.post("/jobs-board/{job_id}/toggle")
def jobs_board_toggle(job_id: int, db: Session = Depends(get_db)):
    row = db.get(JobPosting, job_id)
    row.active = not row.active
    db.commit()
    return RedirectResponse(url="/admin/jobs-board", status_code=303)


@router.get("/health", response_class=HTMLResponse)
def health_view(request: Request, db: Session = Depends(get_db)):
    runs = db.scalars(select(JobRun).order_by(JobRun.started.desc()).limit(20)).all()
    sources = db.scalars(select(SourceHealth).order_by(SourceHealth.source)).all()
    return templates.TemplateResponse(request, "health.html", {"runs": runs, "sources": sources})


@router.get("/subscribers", response_class=HTMLResponse)
def subscribers_view(request: Request, db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Subscriber)) or 0
    return templates.TemplateResponse(request, "subscribers.html", {"count": count})


@router.get("/subscribers/export.csv")
def subscribers_export(db: Session = Depends(get_db)):
    rows = db.scalars(select(Subscriber).order_by(Subscriber.created_at)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["email", "created_at", "hubspot_synced"])
    for r in rows:
        writer.writerow([r.email, r.created_at, r.hubspot_synced])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=subscribers.csv"},
    )
