"""Validate-and-retry pattern for GROQ structured output (Backend Spec §4.2).

Every GROQ call that must return structured data is validated against
a Pydantic model before the response is used anywhere else in the
system (PRD §3.3). On a schema mismatch we retry once with the
validation error appended to the prompt; a second failure raises
LLMValidationFailed so the caller can fall back gracefully instead of
crashing.

GROQ rate-limiting mid-demo is called out as a known risk in the PRD
tech stack, so transport/API errors (429, timeout, connection failure)
are retried with exponential backoff before giving up — a raw 500
from GROQ used to propagate straight through as an unhandled 500 here.
Exhausting retries raises the same LLMValidationFailed callers already
handle, rather than a second error type they'd need to catch.

GROQ occasionally wraps structured output in markdown code fences
(```json ... ```) despite being asked for raw JSON; fences are
stripped before validation, and the retry prompt repeats the
no-fences instruction explicitly.
"""

import time

import groq
from pydantic import BaseModel, ValidationError

from backend.llm.groq_client import call_groq

MAX_TRANSPORT_RETRIES = 2
BACKOFF_BASE_SECONDS = 0.5


class LLMValidationFailed(Exception):
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        super().__init__(f"GROQ response failed to validate against {schema_name} twice")


def _strip_markdown_fences(text: str) -> str:
    """Strip a leading/trailing markdown code fence (```json ... ```) if present."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _call_groq_with_backoff(system_prompt: str, user_prompt: str) -> str | None:
    """Call GROQ, retrying transport/API errors with exponential backoff.

    Returns None once retries are exhausted rather than propagating the
    transport error — callers fall back via LLMValidationFailed, same as
    a schema-validation failure, so there's one failure path to handle.
    """
    for attempt in range(MAX_TRANSPORT_RETRIES + 1):
        try:
            return call_groq(system_prompt, user_prompt)
        except groq.APIError:
            if attempt == MAX_TRANSPORT_RETRIES:
                return None
            time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
    return None


def call_and_validate(system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> BaseModel:
    raw = _call_groq_with_backoff(system_prompt, user_prompt)
    if raw is None:
        raise LLMValidationFailed(schema.__name__)

    try:
        return schema.model_validate_json(_strip_markdown_fences(raw))
    except ValidationError as e:
        retry_prompt = (
            f"{user_prompt}\n\nYour last response didn't match this schema, fix it:\n{e}\n\n"
            "Respond with raw JSON only — no markdown code fences."
        )
        raw_retry = _call_groq_with_backoff(system_prompt, retry_prompt)
        if raw_retry is None:
            raise LLMValidationFailed(schema.__name__)

        try:
            return schema.model_validate_json(_strip_markdown_fences(raw_retry))
        except ValidationError:
            raise LLMValidationFailed(schema.__name__)  # caller falls back gracefully, §4.3
