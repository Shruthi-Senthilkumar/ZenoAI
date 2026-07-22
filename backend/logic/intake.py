"""Adaptive Diagnostic Intake (Backend Spec §7, PRD §4.3).

Branching, one question at a time. Stops asking about a topic once
confidence in the student's level is high, so known material is never
re-taught. Captures target role (SDE/Data/Core) and weekly hours; exam
dates are pulled from the LMS Connector rather than asked here.

Subhiksha's DB isn't live yet, so intake state is stubbed with an
in-memory dict keyed by student_id — swap-in-ready for a real DB later,
same pattern as Phase 1's readiness stub.
"""

from pydantic import BaseModel

from backend.llm.validation import LLMValidationFailed, call_and_validate
from backend.schemas.intake import IntakeTurnResponse

INTAKE_SYSTEM_PROMPT = """You are ZenoAI's adaptive diagnostic intake assistant.

Ask the student ONE question at a time to assess their academic and career
starting point. Branch based on their prior answers — never ask about a
topic again once their answers show high confidence in it.

You must capture, over the course of the conversation:
- target role (SDE / Data / Core)
- weekly hours available for study/practice

Never ask about exam dates — those come from the LMS Connector, not this
conversation.

Once you have enough signal to stop (target role and weekly hours captured,
and no more topics need probing), set "done": true and "next_question": null.

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"next_question": "<string or null>", "quick_replies": ["<string>", ...], "done": <bool>}
"""


class IntakeState(BaseModel):
    answers: list[str] = []
    last_question: str | None = None
    done: bool = False


class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (intake_state table)."""

    def __init__(self) -> None:
        self._STATE: dict[str, IntakeState] = {}

    def get_intake_state(self, student_id: str) -> IntakeState:
        if student_id not in self._STATE:
            self._STATE[student_id] = IntakeState()
        return self._STATE[student_id]

    def save_intake_state(self, student_id: str, state: IntakeState) -> None:
        self._STATE[student_id] = state


db = _StubDB()


def build_intake_prompt(state: IntakeState) -> str:
    if not state.answers:
        return "This is the start of the intake conversation. Ask the first question."

    history_lines = []
    if state.last_question:
        history_lines.append(f"Q: {state.last_question}")
    history_lines.append(f"A: {state.answers[-1]}")
    history = "\n".join(history_lines)

    prior_answers = ", ".join(state.answers[:-1]) if len(state.answers) > 1 else "none yet"

    return (
        f"Prior answers so far: {prior_answers}\n"
        f"Most recent exchange:\n{history}\n\n"
        "Based on this, ask the next branching question, or set done=true if you "
        "now have enough signal (target role, weekly hours, and topic confidence)."
    )


def next_intake_turn(student_id: str, last_answer: str) -> IntakeTurnResponse:
    state = db.get_intake_state(student_id)
    if last_answer:
        state.answers.append(last_answer)

    prompt = build_intake_prompt(state)
    try:
        response = call_and_validate(INTAKE_SYSTEM_PROMPT, prompt, IntakeTurnResponse)
    except LLMValidationFailed:
        # Fallback (§4.3): re-ask the same question, slightly reworded, never crash.
        fallback_question = state.last_question or "Could you tell me a bit about your background?"
        response = IntakeTurnResponse(
            next_question=f"Sorry, let me ask that a different way: {fallback_question}",
            quick_replies=[],
            done=False,
        )

    state.last_question = response.next_question
    state.done = response.done
    db.save_intake_state(student_id, state)
    return response
