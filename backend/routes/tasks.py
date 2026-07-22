"""GET /tasks/today, POST /tasks/{id}/complete (item 6 — the core loop's backend)."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.tasks import TodayResponse, complete_task, get_today_response

router = APIRouter()


class TaskCompleteRequest(BaseModel):
    student_id: str


@router.get("/tasks/today", response_model=TodayResponse)
def get_tasks_today(student_id: str) -> TodayResponse:
    return get_today_response(student_id)


@router.post("/tasks/{task_id}/complete")
def post_task_complete(task_id: str, payload: TaskCompleteRequest) -> dict:
    complete_task(payload.student_id, task_id)
    return {"status": "ok"}
