"""GET /notifications (PRD §4.17, Frontend Spec §6 API Contract)."""

from fastapi import APIRouter

from backend.logic.notifications import get_active_notification

router = APIRouter()


@router.get("/notifications")
def get_notifications(student_id: str) -> dict:
    banner = get_active_notification(student_id)
    return {"banner": banner.model_dump() if banner else None}
