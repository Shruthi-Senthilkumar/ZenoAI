import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database import Student, create_or_update_student, engine, init_db
from backend.logic.crypto import decrypt_token
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    # Bare TestClient(app) (no `with` block) never fires main.py's
    # @app.on_event("startup") hook, so seed_db()'s student rows never
    # get created here — only init_db()'s schema does. Seed the two
    # students these tests actually need directly, rather than
    # depending on the full seed flow or switching every test in this
    # file to a `with` block just for this.
    init_db()
    create_or_update_student(student_id="student_a", name="Test Student A")
    create_or_update_student(student_id="student_b", name="Test Student B")


def test_authorize_redirects_to_github_with_state():
    response = client.get("/auth/github/authorize?student_id=student_a", follow_redirects=False)
    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://github.com/login/oauth/authorize")
    assert "state=" in location
    assert "scope=repo" in location


def test_authorize_requires_configured_client_id(monkeypatch):
    monkeypatch.delenv("GITHUB_OAUTH_CLIENT_ID", raising=False)
    response = client.get("/auth/github/authorize?student_id=student_a", follow_redirects=False)
    assert response.status_code == 500


def test_callback_rejects_unknown_state():
    """A forged or expired state must never store a token — this is
    OAuth's CSRF protection, not decoration."""
    response = client.get(
        "/auth/github/callback?code=irrelevant&state=never-issued", follow_redirects=False
    )
    assert response.status_code in (302, 307)
    assert "github=state_mismatch" in response.headers["location"]


def test_callback_exchanges_code_and_stores_encrypted_token(monkeypatch):
    authorize_response = client.get(
        "/auth/github/authorize?student_id=student_a", follow_redirects=False
    )
    state = authorize_response.headers["location"].split("state=")[1]

    class FakeTokenResponse:
        status_code = 200

        def json(self):
            return {"access_token": "gho_faketoken123"}

    class FakeUserResponse:
        status_code = 200

        def json(self):
            return {"login": "student-a-real-username"}

    class FakeHTTPXClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, **kwargs):
            return FakeTokenResponse()

        def get(self, url, **kwargs):
            return FakeUserResponse()

    monkeypatch.setattr("backend.routes.auth.httpx.Client", lambda: FakeHTTPXClient())

    response = client.get(
        f"/auth/github/callback?code=fake_code&state={state}", follow_redirects=False
    )
    assert response.status_code in (302, 307)
    assert "github=connected" in response.headers["location"]

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == "student_a")).first()
        assert student.github_token_encrypted is not None
        assert decrypt_token(student.github_token_encrypted) == "gho_faketoken123"
        assert student.github_username == "student-a-real-username"


def test_status_reflects_connected_state_after_callback(monkeypatch):
    authorize_response = client.get(
        "/auth/github/authorize?student_id=student_b", follow_redirects=False
    )
    state = authorize_response.headers["location"].split("state=")[1]

    class FakeTokenResponse:
        status_code = 200

        def json(self):
            return {"access_token": "gho_anothertoken"}

    class FakeUserResponse:
        status_code = 200

        def json(self):
            return {"login": "student-b-real-username"}

    class FakeHTTPXClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, **kwargs):
            return FakeTokenResponse()

        def get(self, url, **kwargs):
            return FakeUserResponse()

    monkeypatch.setattr("backend.routes.auth.httpx.Client", lambda: FakeHTTPXClient())
    client.get(f"/auth/github/callback?code=fake_code&state={state}", follow_redirects=False)

    status = client.get("/auth/github/status?student_id=student_b").json()
    assert status == {"connected": True, "github_username": "student-b-real-username"}


def test_decrypt_token_returns_none_for_garbage_ciphertext():
    """A rotated/corrupted key must degrade to 'not connected', not a
    500 that takes down whatever route happened to touch it."""
    assert decrypt_token("not-a-real-fernet-token") is None