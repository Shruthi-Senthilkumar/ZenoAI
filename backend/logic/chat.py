"""Mentor AI Chat (Backend Spec §12, §12.1).

Reuses Phase 1's call_and_validate — no chat-specific GROQ client.
CHAT_SYSTEM_PROMPT enforces the coach-not-judge register on every
behavioral signal mentioned, same banned-word rule as the
struggle-detector (§10); reused from struggle_detector.BANNED_WORDS
rather than a second copy of the list, and enforced in code (not just
via the prompt) with the same fallback-to-safe-copy pattern as
_make_offer, so a slip past the prompt instruction can't reach the
student verbatim.

§12.1 Chat History: Rolling Window, Not Full Thread. The full
conversation is never replayed into the prompt — only the last
HISTORY_WINDOW turns. Older turns are dropped, not summarized (an
extra GROQ call to summarize is unnecessary complexity for a 24-hour
session length). Student context (readiness, streak, struggle
signals) is rebuilt fresh on every call rather than accumulated in
history — cheap to recompute, keeps the prompt from carrying stale
numbers forward.

On LLMValidationFailed, returns the UI/UX Spec §6 copy verbatim
("Mentor AI needs a breather...") without touching history — a failed
turn was never really said, so it shouldn't pollute future context or
show up as a real exchange when the user retries.

Subhiksha's DB isn't live yet, so chat history is stubbed with an
in-memory _StubDB — swap-in-ready for a real DB later, same pattern
as prior phases.
"""

from backend.llm.validation import LLMValidationFailed, call_and_validate
from backend.logic.readiness import compute_readiness
from backend.logic.streak import db as streak_db
from backend.logic.struggle_detector import BANNED_WORDS, check_for_struggle_signals
from backend.schemas.chat import ChatReplyResponse

HISTORY_WINDOW = 5  # last N turns only

BREATHER_REPLY = "Mentor AI needs a breather — tap to retry your last message"

CHAT_SYSTEM_PROMPT = """You are Zeno, ZenoAI's Mentor AI — a coach, not a judge.

You have access to the student's recent readiness, streak, and any active
struggle signals in the prompt context. When you reference any of these
signals, translate them into supportive, forward-looking coach language.
Never use the words "stuck," "struggling," or "behind" — describe what's
next, not what's wrong.

Keep replies short and conversational, grounded in the provided context and
recent conversation history.

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"reply": "<string>"}
"""

SAFE_FALLBACK_REPLY = "Let's take the next step together — what would you like to focus on?"


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (chat_history table)."""

    def __init__(self) -> None:
        self._HISTORY: dict[str, list[tuple[str, str]]] = {}

    def get_chat_history(self, student_id: str) -> list[tuple[str, str]]:
        return self._HISTORY.get(student_id, [])

    def append_chat_turn(self, student_id: str, message: str, reply: str) -> None:
        turns = self._HISTORY.setdefault(student_id, [])
        turns.append((message, reply))
        del turns[:-HISTORY_WINDOW]  # trim on write, keep the table small too


db = _StubDB()


def get_recent_history(student_id: str) -> list[tuple[str, str]]:
    return db.get_chat_history(student_id)[-HISTORY_WINDOW:]


def append_to_history(student_id: str, message: str, reply: str) -> None:
    db.append_chat_turn(student_id, message, reply)


def build_context(student_id: str) -> dict:
    """Rebuilt fresh on every call — never accumulated into history."""
    academic = compute_readiness(student_id, "academic")
    career = compute_readiness(student_id, "career")
    struggle_offers = check_for_struggle_signals(student_id)

    return {
        "readiness": {
            "academic": {"score": academic.score, "confidence": academic.confidence},
            "career": {"score": career.score, "confidence": career.confidence},
        },
        "streak": {
            "count": streak_db.get_streak_count(student_id),
            "academic_done_today": streak_db.today_academic_task_completed(student_id),
            "career_active_today": streak_db.today_github_or_leetcode_activity(student_id),
        },
        "struggle_signals": [{"topic": o.topic, "reason": o.reason} for o in struggle_offers],
    }


def build_chat_prompt(history: list[tuple[str, str]], context: dict, message: str) -> str:
    history_lines = [f"Student: {m}\nZeno: {r}" for m, r in history]
    history_block = "\n".join(history_lines) if history_lines else "(no prior turns)"

    return (
        f"Student context: {context}\n\n"
        f"Recent conversation:\n{history_block}\n\n"
        f"Student: {message}\n"
        "Reply as Zeno."
    )


def _contains_banned_word(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in BANNED_WORDS)


def chat_reply(student_id: str, message: str) -> ChatReplyResponse:
    context = build_context(student_id)
    history = get_recent_history(student_id)
    prompt = build_chat_prompt(history, context, message)

    try:
        reply = call_and_validate(CHAT_SYSTEM_PROMPT, prompt, ChatReplyResponse)
    except LLMValidationFailed:
        return ChatReplyResponse(reply=BREATHER_REPLY)

    if _contains_banned_word(reply.reply):
        reply = ChatReplyResponse(reply=SAFE_FALLBACK_REPLY)

    append_to_history(student_id, message, reply.reply)
    return reply
