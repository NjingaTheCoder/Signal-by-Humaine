import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.admin.router import router as admin_router
from app.api import briefing, funding, health, jobs, news, quotes, resources, subscribe, tenders
from app.scheduler import register_jobs, scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("signal.main")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_jobs()
    scheduler.start()
    logger.info("scheduler started with %d jobs", len(scheduler.get_jobs()))
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Signal by Humaine", lifespan=lifespan)

# API routes first — mounted under /api
app.include_router(health.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(funding.router, prefix="/api")
app.include_router(tenders.router, prefix="/api")
app.include_router(quotes.router, prefix="/api")
app.include_router(briefing.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(subscribe.router, prefix="/api")

# Admin routes next — mounted under /admin
app.include_router(admin_router, prefix="/admin")

# SPA static mount LAST so it never shadows /api or /admin routes
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.warning("static dir %s does not exist yet; run `npm run build` in web/", STATIC_DIR)
