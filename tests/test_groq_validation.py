import os

import groq
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


def test_call_groq_uses_a_sane_default_model_when_env_var_unset(monkeypatch):
    # item 5 regression: model=os.getenv("GROQ_MODEL") was None if unset,
    # which the Groq SDK would reject outright.
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    captured = {}

    class FakeCompletions:
        def create(self, model, messages):
            captured["model"] = model

            class Choice:
                class message:
                    content = "hi"

            class Response:
                choices = [Choice()]

            return Response()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(groq_client, "_get_client", lambda: FakeClient())

    groq_client.call_groq("system", "user")

    assert captured["model"] == groq_client.DEFAULT_GROQ_MODEL


def test_strip_markdown_fences_removes_json_code_fence():
    from backend.llm.validation import _strip_markdown_fences

    fenced = '```json\n{"message": "hi"}\n```'
    assert _strip_markdown_fences(fenced) == '{"message": "hi"}'


def test_strip_markdown_fences_leaves_plain_json_untouched():
    from backend.llm.validation import _strip_markdown_fences

    plain = '{"message": "hi"}'
    assert _strip_markdown_fences(plain) == plain


def test_call_and_validate_strips_fences_before_validating(monkeypatch):
    def fenced_response(system_prompt, user_prompt):
        return '```json\n{"message": "fenced but valid"}\n```'

    monkeypatch.setattr("backend.llm.validation.call_groq", fenced_response)

    result = call_and_validate(
        system_prompt=ECHO_SYSTEM_PROMPT,
        user_prompt="anything",
        schema=Echo,
    )

    assert result == Echo(message="fenced but valid")


def test_call_and_validate_retries_transport_error_then_succeeds(monkeypatch):
    import httpx

    import backend.llm.validation as validation_module

    monkeypatch.setattr(validation_module.time, "sleep", lambda _: None)

    calls = []

    def flaky_call_groq(system_prompt, user_prompt):
        calls.append(1)
        if len(calls) == 1:
            raise groq.APIConnectionError(request=httpx.Request("POST", "https://api.groq.com/x"))
        return '{"message": "recovered after retry"}'

    monkeypatch.setattr("backend.llm.validation.call_groq", flaky_call_groq)

    result = call_and_validate(
        system_prompt=ECHO_SYSTEM_PROMPT,
        user_prompt="anything",
        schema=Echo,
    )

    assert result == Echo(message="recovered after retry")
    assert len(calls) == 2


def test_call_and_validate_raises_llm_validation_failed_after_exhausting_transport_retries(monkeypatch):
    import httpx

    import backend.llm.validation as validation_module

    monkeypatch.setattr(validation_module.time, "sleep", lambda _: None)

    def always_fails(system_prompt, user_prompt):
        raise groq.APIConnectionError(request=httpx.Request("POST", "https://api.groq.com/x"))

    monkeypatch.setattr("backend.llm.validation.call_groq", always_fails)

    # a raw GROQ transport error must never propagate — callers only ever
    # need to handle LLMValidationFailed, not a second exception type
    with pytest.raises(LLMValidationFailed):
        call_and_validate(
            system_prompt=ECHO_SYSTEM_PROMPT,
            user_prompt="anything",
            schema=Echo,
        )
