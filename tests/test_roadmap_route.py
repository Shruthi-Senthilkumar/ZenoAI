from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.logic.tasks import get_today_tasks
from backend.routes.roadmap import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_roadmap_route_matches_grouped_by_date_contract_shape():
    body = client.get("/roadmap", params={"student_id": "student-1"}).json()

    assert set(body.keys()) == {"days"}
    assert len(body["days"]) > 0
    for group in body["days"]:
        assert set(group.keys()) == {"date", "items"}
        assert isinstance(group["items"], list)
        for item in group["items"]:
            assert set(item.keys()) == {"id", "goalType", "title", "reason", "status"}


def test_roadmap_route_groups_multiple_items_under_the_same_date():
    body = client.get("/roadmap", params={"student_id": "student-1"}).json()

    first_group = body["days"][0]
    # student-1's fixture produces both an academic and a career item today
    assert len(first_group["items"]) >= 2
    goal_types = {item["goalType"] for item in first_group["items"]}
    assert goal_types == {"academic", "career"}


def test_roadmap_route_dates_are_in_chronological_order():
    body = client.get("/roadmap", params={"student_id": "student-1"}).json()
    dates = [g["date"] for g in body["days"]]
    assert dates == sorted(dates)


def test_roadmap_route_task_ids_match_tasks_today_ids_for_the_same_day():
    # roadmap.py and tasks.py share roadmap_day_to_task_item() (item 6/9) so
    # a roadmap item and its corresponding Today task must be the same task.
    roadmap_body = client.get("/roadmap", params={"student_id": "student-1"}).json()
    today_ids = {t.id for t in get_today_tasks("student-1")}

    first_day_ids = {item["id"] for item in roadmap_body["days"][0]["items"]}
    assert first_day_ids.issubset(today_ids)
