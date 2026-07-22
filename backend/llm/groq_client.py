"""Single GROQ wrapper (Backend Spec §4.1).

Every GROQ call in the app routes through `call_groq` — no feature
ever calls the Groq SDK directly.

GROQ_BACKUP_MODE=ollama was documented in .env.example but never
implemented anywhere — a mitigation that doesn't exist is worse than
none, so it's been removed from .env.example rather than left as a
misleading no-op. A real local-Ollama fallback would need its own
client, an assumed-running local server, and a parallel code path we
have no way to test in this environment; if that's wanted later it
belongs here, behind an explicit GROQ_BACKUP_MODE check.
"""

import os

from groq import Groq

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def call_groq(system_prompt: str, user_prompt: str) -> str:
    response = _get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
