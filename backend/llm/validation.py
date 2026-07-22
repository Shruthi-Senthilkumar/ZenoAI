"""Validate-and-retry pattern for GROQ structured output (Backend Spec §4.2).

Every GROQ call that must return structured data is validated against
a Pydantic model before the response is used anywhere else in the
system (PRD §3.3). On a schema mismatch we retry once with the
validation error appended to the prompt; a second failure raises
LLMValidationFailed so the caller can fall back gracefully instead of
crashing.
"""

from pydantic import BaseModel, ValidationError

from backend.llm.groq_client import call_groq


class LLMValidationFailed(Exception):
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        super().__init__(f"GROQ response failed to validate against {schema_name} twice")


def call_and_validate(system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> BaseModel:
    raw = call_groq(system_prompt, user_prompt)
    try:
        return schema.model_validate_json(raw)
    except ValidationError as e:
        retry_prompt = f"{user_prompt}\n\nYour last response didn't match this schema, fix it:\n{e}"
        raw_retry = call_groq(system_prompt, retry_prompt)
        try:
            return schema.model_validate_json(raw_retry)
        except ValidationError:
            raise LLMValidationFailed(schema.__name__)  # caller falls back gracefully, §4.3
