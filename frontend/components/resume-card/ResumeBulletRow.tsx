"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ResumeBullet, ResumeFeedbackOutcome } from "@/lib/types";

// Shared between components/resume-card/ResumeCard.tsx (Dashboard) and
// app/(app)/goals/page.tsx's resume-in-progress list — one row renderer,
// same POST /resume/bullets/{id}/feedback wiring (confirmed live) in both
// places.
export function ResumeBulletRow({ bullet }: { bullet: ResumeBullet }) {
  const [feedbackSent, setFeedbackSent] = useState<ResumeFeedbackOutcome | null>(null);

  function sendFeedback(outcome: ResumeFeedbackOutcome) {
    api
      .post(`/resume/bullets/${bullet.id}/feedback`, { outcome })
      .then(() => setFeedbackSent(outcome))
      .catch(() => setFeedbackSent(null));
  }

  return (
    <div className="resume-card">
      <p>&quot;{bullet.text}&quot;</p>
      <div className="feedback-row">
        <button onClick={() => navigator.clipboard.writeText(bullet.text)}>Copy</button>
        {feedbackSent ? (
          <span>Thanks — recorded as &quot;{feedbackSent}&quot;.</span>
        ) : (
          <>
            Did this help in an interview?
            <button onClick={() => sendFeedback("yes")}>Yes</button>
            <button onClick={() => sendFeedback("no")}>No</button>
            <button onClick={() => sendFeedback("somewhat")}>Somewhat</button>
          </>
        )}
      </div>
    </div>
  );
}
