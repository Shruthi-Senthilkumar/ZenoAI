import pytest

from backend.logic.intake import IntakeState, db, next_intake_turn
from backend.llm.validation import LLMValidationFailed
from backend.schemas.intake import IntakeTurnResponse


@pytest.fixture(autouse=True)
def _reset_stub_db():
    db._STATE.clear()
    yield
    db._STATE.clear()


def test_first_turn_has_no_answer_yet_and_asks_a_question(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        assert schema is IntakeTurnResponse
        return IntakeTurnResponse(
            next_question="What role are you targeting? (SDE / Data / Core)",
            quick_replies=["SDE", "Data", "Core"],
            done=False,
        )

    monkeypatch.setattr("backend.logic.intake.call_and_validate", fake_call_and_validate)

    response = next_intake_turn("student-x", last_answer="")

    assert response.done is False
    assert response.next_question is not None
    state = db.get_intake_state("student-x")
    assert state.answers == []  # empty first answer is not recorded
    assert state.last_question == response.next_question


def test_state_updates_append_answers_across_turns(monkeypatch):
    calls = []

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        calls.append(user_prompt)
        return IntakeTurnResponse(next_question="Rate your comfort with OOP:", quick_replies=[], done=False)

    monkeypatch.setattr("backend.logic.intake.call_and_validate", fake_call_and_validate)

    next_intake_turn("student-y", last_answer="")
    next_intake_turn("student-y", last_answer="SDE")
    next_intake_turn("student-y", last_answer="confident")

    state = db.get_intake_state("student-y")
    assert state.answers == ["SDE", "confident"]
    # second and third calls should carry conversation history in the prompt
    assert "SDE" in calls[2]


def test_branching_stops_when_llm_signals_done(monkeypatch):
    def fake_call_and_validate(system_prompt, user_prompt, schema):
        return IntakeTurnResponse(next_question=None, quick_replies=[], done=True)

    monkeypatch.setattr("backend.logic.intake.call_and_validate", fake_call_and_validate)

    response = next_intake_turn("student-z", last_answer="confident")

    assert response.done is True
    assert response.next_question is None
    state = db.get_intake_state("student-z")
    assert state.done is True


def test_fallback_on_validation_failure_never_crashes(monkeypatch):
    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.intake.call_and_validate", raise_validation_failed)

    state = db.get_intake_state("student-fallback")
    state.last_question = "What role are you targeting?"
    db.save_intake_state("student-fallback", state)

    response = next_intake_turn("student-fallback", last_answer="uh")

    assert isinstance(response, IntakeTurnResponse)
    assert response.done is False
    assert response.next_question is not None
    assert "What role are you targeting?" in response.next_question


def test_fallback_state_is_saved_and_conversation_can_continue(monkeypatch):
    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.intake.call_and_validate", raise_validation_failed)

    response = next_intake_turn("student-continue", last_answer="")
    state = db.get_intake_state("student-continue")
    assert state.last_question == response.next_question
    assert state.done is False
