"""Resume Bullet generation (Backend Spec §3, §4.3; PRD §4.19, UI/UX Spec §8.9).

Fires only on a verified module/project completion. Reuses Phase 1's
call_and_validate — no separate GROQ client. Storage stays Subhiksha's
(Integration Spec §4/§9) — this generates and returns, it never
persists to a real table.

Fallback (§4.3): on LLMValidationFailed, defer generation to the next
completed-module trigger — return None rather than showing a partial
bullet. Unlike quiz_gen's empty-questions sentinel, a resume bullet
has no meaningful "empty but valid" shape, so the fallback signal here
is genuinely Optional rather than a same-type placeholder.

On a genuine success (never on a deferred failure), also flips
notifications.py's resume-bullet-ready flag (PRD §4.17) — see
docs/BACKEND_SPEC_ADDENDUM.md §14 for why that flag previously never
fired.
"""

from backend.llm.validation import LLMValidationFailed, call_and_validate
from backend.logic.notifications import db as notifications_db
from backend.schemas.resume import ResumeBulletResponse

RESUME_SYSTEM_PROMPT = """You write concise, resume-ready bullet points for students,
based on a module or project they just completed.

One bullet, action-verb-led, quantified where the evidence supports it,
suitable for pasting straight into a resume. Use the evidence_link exactly
as given in the prompt — never invent a different one.

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"text": "<string>", "evidence_link": "<string>"}
"""


def generate_resume_bullet(student_id: str, completed_topic: str, evidence_link: str) -> ResumeBulletResponse | None:
    try:
        result = call_and_validate(
            RESUME_SYSTEM_PROMPT,
            f"Completed topic: {completed_topic}\nEvidence link: {evidence_link}\nWrite one resume bullet.",
            ResumeBulletResponse,
        )
    except LLMValidationFailed:
        return None  # §4.3: defer to next completed-module trigger, no partial bullet shown

    # Item 2 (master prompt): only a successful generation should ever make
    # the resume-bullet-ready banner (PRD §4.17) eligible to fire — a
    # deferred/failed attempt must not.
    notifications_db.mark_resume_bullet_ready(student_id)
    return result
