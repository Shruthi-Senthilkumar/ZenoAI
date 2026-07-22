import os

import pytest
from pydantic import BaseModel, ValidationError

from backend.llm import groq_client
from backend.llm.validation import LLMValidationFailed, call_and_validate

requires_live_groq = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set; live GROQ checkpoint test skipped",
)


class Echo(BaseModel):
    """Trivial schema used to prove the wrapper + validation pattern."""

    message: str


ECHO_SYSTEM_PROMPT = (
    "You reply with ONLY raw JSON, no markdown fences, no prose. "
    'The JSON must match exactly: {"message": "<string>"}'
)


@requires_live_groq
def test_call_groq_hits_the_real_api_and_returns_text():
    reply = groq_client.call_groq(
        system_prompt="You are a helpful assistant. Reply in one short sentence.",
        user_prompt="Say hello in exactly three words.",
    )
    assert isinstance(reply, str)
    assert len(reply.strip()) > 0


@requires_live_groq
def test_call_and_validate_real_call_matches_trivial_schema():
    result = call_and_validate(
        system_prompt=ECHO_SYSTEM_PROMPT,
        user_prompt='Respond with JSON: {"message": "hello from groq"}',
        schema=Echo,
    )
    assert isinstance(result, Echo)
    assert isinstance(result.message, str)
    assert len(result.message) > 0


def test_call_and_validate_retries_once_then_succeeds(monkeypatch):
    responses = iter(['{"not_message": "oops"}', '{"message": "fixed on retry"}'])
    calls = []

    def fake_call_groq(system_prompt, user_prompt):
        calls.append(user_prompt)
        return next(responses)

    monkeypatch.setattr("backend.llm.validation.call_groq", fake_call_groq)

    result = call_and_validate(
        system_prompt=ECHO_SYSTEM_PROMPT,
        user_prompt='Respond with JSON: {"message": "..."}',
        schema=Echo,
    )

    assert result == Echo(message="fixed on retry")
    assert len(calls) == 2
    assert "didn't match this schema" in calls[1]


def test_call_and_validate_raises_after_second_failure(monkeypatch):
    def always_bad(system_prompt, user_prompt):
        return '{"not_message": "still wrong"}'

    monkeypatch.setattr("backend.llm.validation.call_groq", always_bad)

    with pytest.raises(LLMValidationFailed) as exc_info:
        call_and_validate(
            system_prompt=ECHO_SYSTEM_PROMPT,
            user_prompt='Respond with JSON: {"message": "..."}',
            schema=Echo,
        )
    assert exc_info.value.schema_name == "Echo"
