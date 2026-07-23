"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { IntakeTurnResponse } from "@/lib/types";

// No auth/session layer exists in this repo — same placeholder gap as
// app/(app)/layout.tsx's PLACEHOLDER_STUDENT_ID, flagged there and in the
// final report. Intake deliberately doesn't touch the Zustand store (see
// app/(onboarding)/layout.tsx), so it keeps its own copy of the constant
// rather than reaching into app/(app)'s provider.
const PLACEHOLDER_STUDENT_ID = "student-1";

export default function IntakePage() {
  const router = useRouter();
  const [turn, setTurn] = useState<IntakeTurnResponse | null>(null);
  const [freeText, setFreeText] = useState("");
  const [pending, setPending] = useState(true);
  const [error, setError] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(0);

  function submitTurn(lastAnswer: string) {
    setPending(true);
    setError(false);
    api
      .post<IntakeTurnResponse>("/intake/turn", {
        student_id: PLACEHOLDER_STUDENT_ID,
        last_answer: lastAnswer,
      })
      .then((res) => {
        setTurn(res);
        setQuestionNumber((n) => n + 1);
        setFreeText("");
        if (res.done) router.push("/today");
      })
      .catch(() => setError(true))
      .finally(() => setPending(false));
  }

  useEffect(() => {
    submitTurn("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="intake-shell">
      <div className="intake-progress">
        {turn?.done ? "All set — redirecting…" : questionNumber > 0 ? `Question ${questionNumber}` : "Getting started…"}
      </div>

      <div className="intake-card">
        {pending && !turn && (
          <>
            <div className="skel skel-line w-60" style={{ height: 18, marginBottom: 18 }} />
            <div className="skel skel-line" style={{ height: 40, marginBottom: 8 }} />
          </>
        )}

        {error && (
          <>
            <p className="intake-question">Couldn&apos;t reach the intake service.</p>
            <button className="state-cta" onClick={() => submitTurn("")}>
              Retry
            </button>
          </>
        )}

        {!error && turn && !turn.done && (
          <>
            <p className="intake-question">{turn.next_question}</p>

            {turn.quick_replies.length > 0 && (
              <div className="intake-chips">
                {turn.quick_replies.map((reply) => (
                  <button key={reply} disabled={pending} onClick={() => submitTurn(reply)}>
                    {reply}
                  </button>
                ))}
              </div>
            )}

            <div className="intake-free">
              <input
                type="text"
                placeholder="Or type your own answer…"
                value={freeText}
                disabled={pending}
                onChange={(e) => setFreeText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && freeText.trim() && submitTurn(freeText.trim())}
              />
              <button disabled={pending || !freeText.trim()} onClick={() => submitTurn(freeText.trim())}>
                Send
              </button>
            </div>

            <button className="intake-skip" disabled={pending} onClick={() => submitTurn("")}>
              skip
            </button>

            {pending && (
              <div className="typing-dots" style={{ marginTop: 12 }}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
