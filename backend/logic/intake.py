"""Adaptive Diagnostic Intake (Backend Spec §7, PRD §4.3).

Branching, one question at a time. Captures target role (SDE/Data/
Core), weekly hours, educational qualification, and a per-topic skill
level across 4-6 real skill-tree nodes. Exam dates are pulled from the
LMS Connector rather than asked here.

Topic level is deliberately NOT self-reported. Earlier drafts of this
prompt asked "rate your comfort: never used / used it / confident" —
a self-rating scale, which students routinely over- or under-estimate.
Instead, each topic gets a genuine diagnostic question that tests
actual understanding (e.g. "How would you reverse a linked list?"),
answered in free text, and GROQ classifies beginner/intermediate/
advanced from the *content and correctness* of that answer during
extraction — the student is never asked to grade themselves, and
never even sees "beginner/intermediate/advanced" as a term in the
conversation.

Conversation state itself is still stubbed with an in-memory dict keyed
by student_id — swap-in-ready for a real DB later, same pattern as
Phase 1's readiness stub. Structured extraction is not stubbed: once
the conversation ends (done=true), extract_and_store_profile() runs
one more schema-validated GROQ call over the full transcript and
writes target_role/weekly_hours/education_level/topic_levels to the
real Student row (Subhiksha's DB, backend/database.py).

Known gap, flagged not fixed: topic_levels is evaluated and persisted
(as a JSON string on Student.topic_levels_json), but nothing yet reads
it back into roadmap.py's `satisfied` set — a student diagnosed
"advanced" on arrays still sees arrays scheduled. Wiring that up is
the natural next step, not done here.
"""

import json
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database import Student, create_or_update_student, engine
from backend.llm.validation import LLMValidationFailed, call_and_validate
from backend.schemas.intake import IntakeTurnResponse

INTAKE_SYSTEM_PROMPT = """You are ZenoAI's adaptive diagnostic intake assistant.

Ask the student ONE question at a time. Branch based on their prior answers.

You must capture, over the course of the conversation, in this order:
1. Target role (SDE / Data / Core).
2. Weekly hours available for study/practice.
3. How many months they're planning to commit to this learning plan —
   ask plainly, e.g. "How many months are you planning to invest in
   this?" with quick_replies like ["1 month", "3 months", "6 months",
   "1 year+"]. This is a planning fact, not a skill self-rating.
4. Educational qualification — ask plainly, e.g. "What's your current level
   of study?" with quick_replies like ["High school", "Undergraduate",
   "Graduate", "Working professional"]. This one IS fine to ask directly —
   it's a fact, not a skill self-rating.
5. Diagnostic assessment on exactly 3 topics drawn from these real
   skill-tree nodes, chosen based on their target role:
   - Always include: python-basics
   - If SDE or Core: also arrays, recursion
   - If Data: also linear-algebra, sql

   CRITICAL — how to ask about each topic: never ask the student to rate
   their own skill level (no "how comfortable are you", no "rate yourself",
   no beginner/intermediate/advanced as options). Instead ask ONE genuine,
   concrete question that tests whether they actually understand the
   topic, and let them answer in their own words. Examples of the right
   shape: "How would you reverse a linked list?", "What's the difference
   between a hash table and an array, and when would you use each?",
   "Walk me through how you'd approach a dynamic programming problem."
   Free text is expected; quick_replies for these can offer a couple of
   plausible starting phrases but should never be a self-rating scale.
   Ask each topic ONCE only — never re-ask the same or a rephrased
   version of a topic you've already covered, even if the student's
   answer was short or a quick-reply stub.

The whole conversation is exactly 7 questions: role, hours, timeline
commitment, education, then 3 topics — no more, no fewer. Track how many
you've asked so far from the prior-answers list; set "done": true and
"next_question": null the moment you've asked all 7, regardless of how
thorough the answers were.

Never ask about exam dates — those come from the LMS Connector, not this

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"next_question": "<string or null>", "quick_replies": ["<string>", ...], "done": <bool>}
"""

EXTRACTION_SYSTEM_PROMPT = """You extract structured facts from an intake
conversation transcript, and — for the diagnostic topic questions only —
evaluate the STUDENT's actual demonstrated skill level from the content
and correctness of their free-text answer. Do not trust any self-rating
language the student may have used; judge their understanding directly
from what they wrote, the same way a teacher would grade a short-answer
question.

target_role must be one of exactly: "SDE", "Data", "Core".

weekly_hours must be a plain integer. If a range was given, use the
midpoint, rounded to the nearest whole number.

timeline_months must be a plain integer number of months. Convert phrasing
like "1 year+" to a reasonable integer (e.g. 12); if a range was given, use
the midpoint, rounded to the nearest whole number.

education_level must be one of exactly: "High school", "Undergraduate",
"Graduate", "Working professional". If the transcript doesn't clearly
state one, make your best inference from context (e.g. mentions of a
degree program, job, or age-adjacent context) rather than leaving it
ambiguous.

topic_levels is an object mapping each topic that was genuinely asked
about (skip any topic that was never asked or was skipped by the
conversation) to one of exactly: "beginner", "intermediate", "advanced".
Base this purely on how well their actual answer demonstrates
understanding — a confident-sounding but factually wrong or vague answer
is "beginner", a correct but shallow answer is "intermediate", a correct
and well-explained answer (with a working example, an edge case, or a
tradeoff mentioned) is "advanced".

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"target_role": "<SDE|Data|Core>", "weekly_hours": <integer>,
 "timeline_months": <integer>,
 "education_level": "<High school|Undergraduate|Graduate|Working professional>",
 "topic_levels": {"<topic>": "<beginner|intermediate|advanced>", ...}}
"""


class IntakeState(BaseModel):
    answers: list[str] = []
    last_question: str | None = None
    done: bool = False


class ExtractedProfile(BaseModel):
    target_role: str
    weekly_hours: int
    timeline_months: int
    education_level: str
    topic_levels: dict[str, str] = {}

class _StubDB:
    """In-memory fixture stand-in for Subhiksha's DB layer (intake_state table).
    Conversation-turn state only — the extracted profile itself is written
    to the real Student table, not held here."""

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
        return "This is question 1 of 7. Ask the first question: target role."
    history_lines = []
    if state.last_question:
        history_lines.append(f"Q: {state.last_question}")
    history_lines.append(f"A: {state.answers[-1]}")
    history = "\n".join(history_lines)

    prior_answers = ", ".join(state.answers[:-1]) if len(state.answers) > 1 else "none yet"
    next_question_number = len(state.answers) + 1

    return (
        f"This is question {next_question_number} of 7.\n"
        f"Prior answers so far: {prior_answers}\n"
        f"Most recent exchange:\n{history}\n\n"
        "Ask the next question in the fixed sequence (role, hours, timeline "
        "commitment, education, then 3 topics). If you've now asked 7 "
        "questions total, set done=true and next_question=null instead."
    )



def extract_and_store_profile(student_id: str, state: IntakeState) -> None:
    """Runs once, when intake completes. On extraction failure, the
    Student row simply keeps its existing defaults — same graceful-
    degradation shape as everything else in this codebase (never crash
    the flow over an LLM hiccup).

    intake_completed_at is the real signal GET /intake/profile checks,
    not target_role/weekly_hours themselves — those columns already
    carry non-null defaults ("Software Engineer", 15) for every seeded
    student, so a null-check on them would never correctly report
    "hasn't done intake yet" even for a student who genuinely hasn't.
    """
    if not state.answers:
        return

    transcript = "\n".join(f"- {a}" for a in state.answers)
    try:
        extracted = call_and_validate(
            EXTRACTION_SYSTEM_PROMPT,
            f"Intake transcript:\n{transcript}",
            ExtractedProfile,
        )
    except LLMValidationFailed:
        return

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        name = student.name if student else student_id
    create_or_update_student(
        student_id=student_id,
        name=name,
        target_role=extracted.target_role,
        weekly_hours=extracted.weekly_hours,
        timeline_months=extracted.timeline_months,
        education_level=extracted.education_level,
        topic_levels_json=json.dumps(extracted.topic_levels),
        intake_completed_at=datetime.utcnow().isoformat() + "Z",
    )

MAX_INTAKE_QUESTIONS = 7  # role, hours, timeline, education, 3 diagnostic topics — see INTAKE_SYSTEM_PROMPT

def next_intake_turn(student_id: str, last_answer: str) -> IntakeTurnResponse:
    state = db.get_intake_state(student_id)

    # The frontend always posts last_answer="" on page mount (both first-
    # ever visit and every "Retake Intake" click) — React state resets on
    # navigation, so an empty answer genuinely means "the user is
    # starting fresh right now," not "resume." Without this, a student
    # who already completed intake once (state.done=True, answers >= 6)
    # would hit the MAX_INTAKE_QUESTIONS cap on their very first call and
    # get redirected straight back to /today before ever seeing a
    # question — confirmed happening in practice, not hypothetical.
    if not last_answer and state.done:
        state = IntakeState()
        db.save_intake_state(student_id, state)

    if last_answer:
        state.answers.append(last_answer)
    # Hard cap, enforced in code — not just prompt instruction. GROQ's
    # own "have I asked enough" judgment is unreliable this many turns
    # deep (it only ever sees a compressed prior-answers string, no
    # structured topic tracker), and was observed asking 40 questions in
    # practice, repeating similar topics without realizing it already
    # had. This guarantees the conversation genuinely ends at 6
    # regardless of what any single LLM response decides.
    if len(state.answers) >= MAX_INTAKE_QUESTIONS:
        response = IntakeTurnResponse(next_question=None, quick_replies=[], done=True)
        state.last_question = None
        state.done = True
        db.save_intake_state(student_id, state)
        extract_and_store_profile(student_id, state)
        return response

    prompt = build_intake_prompt(state)
    try:
        response = call_and_validate(INTAKE_SYSTEM_PROMPT, prompt, IntakeTurnResponse)
    except LLMValidationFailed:
        fallback_question = state.last_question or "Could you tell me a bit about your background?"
        response = IntakeTurnResponse(
            next_question=f"Sorry, let me ask that a different way: {fallback_question}",
            quick_replies=[],
            done=False,
        )

    state.last_question = response.next_question
    state.done = response.done
    db.save_intake_state(student_id, state)

    if response.done:
        extract_and_store_profile(student_id, state)

    return response


