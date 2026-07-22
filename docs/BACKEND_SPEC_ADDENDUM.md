**ZENOAI**

*Backend Spec Addendum — §13, §14*

**Owner: Shruthi (Backend/AI)**

Companion to `ZenoAI_Backend_Spec_Shruthi.docx`. Every other feature Shruthi
owns gets a numbered section with a code excerpt in that document — DAG §5,
roadmap §6, intake §7, quiz-gen §8, streak §9, struggle-detector §10,
readiness §11, chat §12. Two owned features shipped with working, tested
code but were never written up there. This file closes that gap without
touching the original document.

# **13. Performance Analytics Dashboard**

*PRD §4.13. Shared surface: Shruthi wires the readiness numbers; trend
history ownership moves to Subhiksha once her DB is live.*

`GET /dashboard/{student_id}` assembles one response from pieces that
already exist elsewhere in this codebase — it introduces no new scoring
logic of its own.

```python
# backend/routes/dashboard.py
from fastapi import APIRouter

from backend.logic.readiness import compute_readiness
from backend.logic.streak import db as streak_db

router = APIRouter()

@router.get("/dashboard/{student_id}")
def get_dashboard(student_id: str):
    academic = compute_readiness(student_id, "academic")
    career = compute_readiness(student_id, "career")
    return {
        "academic": {"readiness": academic.score, "confidence": academic.confidence,
                      "trend": []},   # stubbed — Subhiksha's trend history, not live yet
        "career": {"readiness": career.score, "confidence": career.confidence,
                    "streak": streak_db.get_streak_count(student_id), "trend": []},
    }
```

- Reuses Phase 1's `compute_readiness()` exactly — academic and career are
  computed separately and never blended, matching PRD §3.5/§12.
- Subject/activity trend arrays are stubbed as empty lists. This is
  deliberate, not an oversight: trend history is normalized data Subhiksha's
  connectors write (Integration Spec §4, `learning_profile`/`github_activity`
  tables), and this route has no DB to read it from yet. When her layer is
  live, only the trend-fetch lines here change — the readiness wiring does
  not.
- Empty-state rule (UI/UX Spec §6): a student with zero evidence must never
  see a bare `0%`. The existing `confidence: "low"` signal from
  `compute_readiness` is sufficient for the frontend to render the
  wide-confidence-band empty state (UI/UX Spec §4.4). No separate
  empty-state field is invented here.

**Definition of Done:** both readiness numbers compute correctly against
seeded profiles once Subhiksha's data layer is live (matches Backend Spec
§13 Final checkpoint) — unchanged from the original document, restated here
because this section didn't previously exist to state it in.

# **14. Outcome Feedback Loop**

*PRD §4.19. Assigned to Shruthi explicitly in the PRD's own Phase 4 table
(§5) — this was a documentation gap, not a scoping question; the task was
always hers.*

Lightweight check-in fired after a resume bullet is shown, closing the loop
on whether the product delivered real value. Storage of the bullet itself
stays Subhiksha's (Integration Spec §4/§9, `resume_bullets.outcome_feedback`
column) — this module only captures the check-in response.

```python
# backend/logic/feedback.py
from pydantic import BaseModel

from backend.schemas.feedback import OutcomeFeedback

class OutcomeFeedbackEvent(BaseModel):
    bullet_id: str
    outcome: OutcomeFeedback   # "yes" | "no" | "somewhat"

def record_outcome_feedback(bullet_id: str, outcome: OutcomeFeedback) -> OutcomeFeedbackEvent:
    event = OutcomeFeedbackEvent(bullet_id=bullet_id, outcome=outcome)
    db.insert(event)   # stubbed; real persistence is Subhiksha's table
    return event
```

- Fires once per bullet, from the UI/UX Spec §4.8 prompt: *"Did this help
  in an interview? [Yes] [No] [Somewhat]"*.
- Intentionally has no relationship to the resume-bullet-ready notification
  flag (§17, below) — one is "a bullet exists," the other is "did the
  bullet work." Keeping them separate means a student can dismiss the
  ready-banner without that being misread as feedback.

**Definition of Done:** a feedback event round-trips against
`resume_bullets.outcome_feedback` once Subhiksha's storage is live —
matches Integration Spec §9 Checkpoint 3's own criterion for this same
column, restated here for symmetry with §13 above.

# **Related fix, not a new feature: the resume-bullet-ready notification wire**

Not a PRD feature in its own right, but worth recording here since it was
found while writing this addendum. `notifications.py`'s
`resume-bullet-ready` banner (PRD §4.17, UI/UX Spec §4.10, priority 2) had
a real, correct priority-ordering implementation — but the flag it read,
`_RESUME_BULLET_READY`, was never set by anything. `resume.py`'s
`generate_resume_bullet` did not know the flag existed. The banner could
never fire, on any input, prior to this fix.

Fixed: `generate_resume_bullet` now calls
`notifications.mark_resume_bullet_ready(student_id)` on a genuine success
only — never on a deferred `LLMValidationFailed` (§4.3's own rule: a
deferred attempt is not a real bullet, so it must not trigger a "ready"
banner). `get_active_notification` clears the flag once it actually
surfaces the banner, so a seen bullet doesn't re-notify on the next poll.
See `tests/test_resume.py`'s three new cases for the full loop, including
the end-to-end path from generation through to `get_active_notification`.
