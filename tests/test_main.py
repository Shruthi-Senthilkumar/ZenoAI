from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXPECTED_PATHS = {
    "/dashboard/{student_id}",
    "/resume/bullets/{bullet_id}/feedback",
    "/intake/turn",
    "/notifications",
    "/push/subscribe",
    "/quiz/generate",
    "/roadmap",
    "/struggle/offers",
    "/struggle/offers/{offer_id}/respond",
    "/tasks/today",
    "/tasks/{task_id}/complete",
}


def test_app_starts_and_docs_are_served():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_lists_every_mounted_route():
    schema = client.get("/openapi.json").json()
    assert EXPECTED_PATHS.issubset(set(schema["paths"].keys()))


def test_cors_allows_localhost_3000():
    response = client.options(
        "/roadmap",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
