import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.llm.validation import LLMValidationFailed
from backend.logic.chat import (
    BREATHER_REPLY,
    HISTORY_WINDOW,
    SAFE_FALLBACK_REPLY,
    build_context,
    chat_reply,
    db,
    get_recent_history,
)
from backend.logic.streak import db as streak_db
from backend.logic.struggle_detector import db as struggle_db
from backend.routes.chat import router
from backend.schemas.chat import ChatReplyResponse

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_stub_dbs():
    db._HISTORY.clear()
    struggle_db._QUIZ_SCORES.clear()
    struggle_db._DAYS_SINCE_LAST_COMMIT.clear()
    yield
    db._HISTORY.clear()
    struggle_db._QUIZ_SCORES.clear()
    struggle_db._DAYS_SINCE_LAST_COMMIT.clear()


def test_chat_reply_returns_validated_response_and_appends_history(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        assert schema is ChatReplyResponse
        return ChatReplyResponse(reply="Let's look at derivatives next.")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)

    result = chat_reply("student-1", "what's next?")

    assert result.reply == "Let's look at derivatives next."
    assert db.get_chat_history("student-1") == [("what's next?", "Let's look at derivatives next.")]


def test_chat_reply_reuses_call_and_validate_not_a_separate_groq_client(monkeypatch):
    called = {}

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        called["used"] = True
        return ChatReplyResponse(reply="ok")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)
    chat_reply("student-1", "hi")

    assert called["used"] is True


def test_chat_reply_on_validation_failure_returns_fixed_copy_and_skips_history(monkeypatch):
    def raise_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.chat.call_and_validate", raise_failed)

    result = chat_reply("student-1", "what's next?")

    assert result.reply == BREATHER_REPLY
    assert db.get_chat_history("student-1") == []  # failed turn never recorded


def test_chat_reply_falls_back_on_banned_word_in_generated_reply(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ChatReplyResponse(reply="You're a bit behind on derivatives.")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)

    result = chat_reply("student-1", "how am I doing?")

    assert result.reply == SAFE_FALLBACK_REPLY
    assert "behind" not in result.reply.lower()
    # the sanitized reply is what gets recorded, not the banned original
    assert db.get_chat_history("student-1") == [("how am I doing?", SAFE_FALLBACK_REPLY)]


def test_get_recent_history_returns_only_the_rolling_window(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ChatReplyResponse(reply=f"reply-{user_prompt[-1]}")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)

    for i in range(HISTORY_WINDOW + 3):
        chat_reply("student-1", f"msg-{i}")

    history = get_recent_history("student-1")
    assert len(history) == HISTORY_WINDOW
    # oldest turns dropped, most recent kept
    assert history[-1][0] == f"msg-{HISTORY_WINDOW + 2}"
    assert history[0][0] == f"msg-{3}"


def test_stub_history_table_is_trimmed_on_write_not_unbounded(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ChatReplyResponse(reply="ok")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)

    for i in range(HISTORY_WINDOW + 10):
        chat_reply("student-1", f"msg-{i}")

    assert len(db.get_chat_history("student-1")) == HISTORY_WINDOW


def test_build_context_is_rebuilt_fresh_reflects_current_state():
    streak_db._STREAK_COUNT["student-1"] = 7
    context_before = build_context("student-1")
    assert context_before["streak"]["count"] == 7

    streak_db._STREAK_COUNT["student-1"] = 9
    context_after = build_context("student-1")
    assert context_after["streak"]["count"] == 9  # not stale, recomputed every call


def test_build_context_includes_struggle_signals_with_banned_word_safe_copy():
    struggle_db._QUIZ_SCORES["student-1"] = []
    struggle_db._DAYS_SINCE_LAST_COMMIT["student-1"] = 5

    context = build_context("student-1")

    assert len(context["struggle_signals"]) == 1
    reason = context["struggle_signals"][0]["reason"]
    for banned in ("stuck", "struggling", "behind"):
        assert banned not in reason.lower()


def test_route_post_chat_message_matches_contract_shape(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return ChatReplyResponse(reply="Here's a good next step.")

    monkeypatch.setattr("backend.logic.chat.call_and_validate", fake_call_and_validate)

    response = client.post("/chat/message", json={"student_id": "student-1", "message": "hi"})

    assert response.status_code == 200
    assert set(response.json().keys()) == {"reply"}
