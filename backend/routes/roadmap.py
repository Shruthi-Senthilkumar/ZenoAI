"""GET /roadmap (Backend Spec §6).

Response shape reconciled with the Frontend Spec §6 API Contract
(item 9): grouped by date, with full TaskItem objects (including id
and status) rather than the flat {day, type, topic, reason} list this
route used to return. Items reuse tasks.py's roadmap_day_to_task_item()
conversion (item 6) so a roadmap item and its corresponding Today task
share the same stable ID and completion status.
"""

from itertools import groupby

from fastapi import APIRouter

from backend.logic.roadmap import generate_roadmap
from backend.logic.tasks import roadmap_day_to_task_item

router = APIRouter()


@router.get("/roadmap")
def get_roadmap(student_id: str) -> dict:
    days = generate_roadmap(student_id)  # already sorted by day (merge_by_day)

    grouped = []
    for date_str, day_items in groupby(days, key=lambda d: d.day):
        task_items = [roadmap_day_to_task_item(student_id, d) for d in day_items]
        grouped.append({"date": date_str, "items": [t.model_dump() for t in task_items]})

    return {"days": grouped}
