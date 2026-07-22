"""POST /push/subscribe (PRD §5, §20 — stretch scope).

NOTE: this path is a documented extension, not yet in the Frontend
Spec §6 API Contract table. Flagged for Thaariha to confirm the
payload shape matches what the frontend's VAPID subscribe flow
actually POSTs — see the PR description.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.push_subscriptions import store_push_subscription

router = APIRouter()


class PushSubscribeRequest(BaseModel):
    student_id: str
    subscription: dict[str, Any]


@router.post("/push/subscribe")
def post_push_subscribe(payload: PushSubscribeRequest) -> dict:
    store_push_subscription(payload.student_id, payload.subscription)
    return {"status": "ok"}
