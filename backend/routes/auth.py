"""GitHub OAuth — GET /auth/github/authorize, GET /auth/github/callback.

Standard OAuth App flow (Integration Spec §6.1): redirect to GitHub's
authorize screen, exchange the returned code for an access token, store
it encrypted at rest against the student row. Framed as an opt-in
upgrade ("track automatically?") — nothing else in the product gates on
this having happened.

`state` carries the student_id through the redirect round-trip, which is
also GitHub OAuth's documented CSRF-protection mechanism — reused for
both purposes rather than inventing a second parameter.
"""
import os
import secrets

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from backend.database import Student, engine
from backend.logic.crypto import encrypt_token

load_dotenv()

router = APIRouter(prefix="/auth/github", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# In-memory state->student_id map for this process's lifetime. A real
# multi-worker deployment would need this in the DB or a shared cache;
# fine for a single-process hackathon backend (same scope decision as
# every other _StubDB in this codebase).
_PENDING_STATE: dict[str, str] = {}


@router.get("/authorize")
def github_authorize(student_id: str = Query(...)):
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID")
    if not client_id:
        raise HTTPException(500, "GITHUB_OAUTH_CLIENT_ID is not configured")

    redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
    state = secrets.token_urlsafe(16)
    _PENDING_STATE[state] = student_id

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "repo",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{query}")


@router.get("/callback")
def github_callback(code: str = Query(...), state: str = Query(...)):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    student_id = _PENDING_STATE.pop(state, None)
    if student_id is None:
        return RedirectResponse(f"{frontend_url}/goals?github=state_mismatch")

    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
    redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

    with httpx.Client() as client:
        token_response = client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return RedirectResponse(f"{frontend_url}/goals?github=exchange_failed")

        user_response = client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github.v3+json"},
        )
        github_username = user_response.json().get("login") if user_response.status_code == 200 else None

    encrypted = encrypt_token(access_token)

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        if student is None:
            return RedirectResponse(f"{frontend_url}/goals?github=unknown_student")
        student.github_token_encrypted = encrypted
        if github_username:
            student.github_username = github_username
        session.add(student)
        session.commit()

    return RedirectResponse(f"{frontend_url}/goals?github=connected")


@router.get("/status")
def github_status(student_id: str = Query(...)) -> dict:
    """Lightweight check the frontend can poll after the redirect lands,
    without needing to parse the query-string flag itself."""
    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        connected = bool(student and student.github_token_encrypted)
        return {
            "connected": connected,
            "github_username": student.github_username if student else None,
        }