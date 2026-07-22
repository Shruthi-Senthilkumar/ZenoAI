"""Single GROQ wrapper (Backend Spec §4.1).

Every GROQ call in the app routes through `call_groq` — no feature
ever calls the Groq SDK directly.
"""

import os

from groq import Groq

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def call_groq(system_prompt: str, user_prompt: str) -> str:
    response = _get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
