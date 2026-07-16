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


def _create_hubspot_contact(email: str, properties: dict, token: str) -> httpx.Response:
    return httpx.post(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {token}"},
        json={"properties": properties},
        timeout=10,
    )


def push_to_hubspot(email: str) -> bool:
    settings = get_settings()
    if not settings.hubspot_access_token:
        return False

    full_properties = {
        "email": email,
        "lifecyclestage": "lead",
        "hs_lead_status": "NEW",
        "signal_source": "signal_terminal",
    }
    try:
        resp = _create_hubspot_contact(email, full_properties, settings.hubspot_access_token)
        if resp.status_code == 409:
            return True
        if resp.status_code == 400:
            # Most likely cause: signal_source is a custom property that doesn't exist in
            # this portal (custom properties must be created in HubSpot's UI first), or
            # lifecyclestage/hs_lead_status aren't configured options there. Retry with only
            # the one field guaranteed to exist on every portal, rather than lose the
            # contact entirely over optional metadata.
            logger.warning("hubspot rejected full contact payload, retrying email-only: %s", resp.text)
            resp = _create_hubspot_contact(email, {"email": email}, settings.hubspot_access_token)
            if resp.status_code == 409:
                return True
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as exc:
        logger.error("hubspot push failed: %s - %s", exc.response.status_code, exc.response.text)
        return False
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
