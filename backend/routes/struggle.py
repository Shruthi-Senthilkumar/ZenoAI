"""GET /struggle/offers, POST /struggle/offers/{id}/respond (Backend Spec §10)."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.struggle_detector import check_for_struggle_signals, log_struggle_correction

router = APIRouter()


class StruggleRespondRequest(BaseModel):
    accepted: bool
    features: dict = {}


@router.get("/struggle/offers")
def get_struggle_offers(student_id: str) -> dict:
    offers = check_for_struggle_signals(student_id)
    return {"offers": [o.model_dump() for o in offers]}


@router.post("/struggle/offers/{offer_id}/respond")
def post_struggle_offer_respond(offer_id: str, payload: StruggleRespondRequest) -> dict:
    log_struggle_correction(offer_id, payload.accepted, payload.features)
    return {"offer_id": offer_id, "logged": True}
