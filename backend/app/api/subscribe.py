import logging

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Subscriber
from app.schemas import SubscribeIn, SubscribeOut

router = APIRouter()
logger = logging.getLogger("signal.api.subscribe")


def push_to_hubspot(email: str) -> bool:
    settings = get_settings()
    if not settings.hubspot_access_token:
        return False
    try:
        resp = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {settings.hubspot_access_token}"},
            json={
                "properties": {
                    "email": email,
                    "lifecyclestage": "lead",
                    "hs_lead_status": "NEW",
                    "signal_source": "signal_terminal",
                }
            },
            timeout=10,
        )
        if resp.status_code == 409:
            return True
        resp.raise_for_status()
        return True
    except Exception:  # noqa: BLE001
        logger.exception("hubspot push failed for subscriber")
        return False


@router.post("/subscribe", response_model=SubscribeOut)
def subscribe(payload: SubscribeIn, db: Session = Depends(get_db)) -> SubscribeOut:
    existing = db.scalar(select(Subscriber).where(Subscriber.email == payload.email))
    if existing is None:
        existing = Subscriber(email=payload.email)
        db.add(existing)
        db.commit()
        db.refresh(existing)

    if not existing.hubspot_synced:
        synced = push_to_hubspot(str(payload.email))
        if synced:
            existing.hubspot_synced = True
            db.commit()

    return SubscribeOut(ok=True)
