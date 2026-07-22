import pytest

from backend.llm.validation import LLMValidationFailed
from backend.logic.quiz_gen import generate_quiz
from backend.schemas.quiz import MicroTestQuestion, MicroTestResponse


def test_generate_quiz_returns_validated_response_from_mocked_groq(monkeypatch):
    fake_response = MicroTestResponse(
        topic="dsa-graphs",
        questions=[
            MicroTestQuestion(q="What is BFS?", options=["Breadth-first search", "Binary flow system"], answer="Breadth-first search"),
            MicroTestQuestion(q="What is DFS?", options=["Depth-first search", "Data flow sync"], answer="Depth-first search"),
            MicroTestQuestion(q="Is a tree a graph?", options=["Yes", "No"], answer="Yes"),
        ],
    )

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        assert schema is MicroTestResponse
        assert "dsa-graphs" in user_prompt
        assert "academic" in user_prompt
        return fake_response

    monkeypatch.setattr("backend.logic.quiz_gen.call_and_validate", fake_call_and_validate)

    result = generate_quiz("dsa-graphs", "academic")

    assert result == fake_response
    assert 3 <= len(result.questions) <= 5


def test_generate_quiz_career_goal_type_is_passed_through(monkeypatch):
    captured = {}

    def fake_call_and_validate(system_prompt, user_prompt, schema):
        captured["user_prompt"] = user_prompt
        return MicroTestResponse(
            topic="git-github",
            questions=[
                MicroTestQuestion(q="What does `git commit` do?", options=["Saves a snapshot", "Deletes history"], answer="Saves a snapshot"),
            ],
        )

    monkeypatch.setattr("backend.logic.quiz_gen.call_and_validate", fake_call_and_validate)

    result = generate_quiz("git-github", "career")

    assert result.topic == "git-github"
    assert "career" in captured["user_prompt"]


def test_generate_quiz_fallback_on_validation_failure_never_crashes(monkeypatch):
    def raise_validation_failed(system_prompt, user_prompt, schema):
        raise LLMValidationFailed(schema.__name__)

    monkeypatch.setattr("backend.logic.quiz_gen.call_and_validate", raise_validation_failed)

    result = generate_quiz("integrals", "academic")

    assert isinstance(result, MicroTestResponse)
    assert result.topic == "integrals"
    assert result.questions == []  # skip signal: no quiz today, prior roadmap state untouched
