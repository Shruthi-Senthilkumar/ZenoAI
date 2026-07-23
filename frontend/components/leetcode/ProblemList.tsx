"use client";

import { useState } from "react";
import { useStudentStore } from "@/lib/store-provider";
import { useLeetCodeProblems } from "@/lib/hooks";
import { DEMO_LEETCODE_PROBLEMS } from "@/lib/demo-data/leetcode";
import { StateBlock } from "@/components/state/StateBlock";
import { TimerChip } from "./TimerChip";
import { PushConfirmButton } from "./PushConfirmButton";

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const DIFF_CLASS: Record<string, string> = { easy: "easy", medium: "med", hard: "" };

// GET /leetcode/problems isn't mounted in backend/routes/ yet. With demo
// mode on, a failed/absent real call falls back to the fixture in
// lib/demo-data/leetcode.ts and shows a loud "Demo data" badge (never
// silently). With demo mode off, a failure renders the same honest
// "not connected" state used by LMS and the Internship Feed. Either way,
// push-confirm still always hits the real (currently unbuilt) endpoint —
// see PushConfirmButton.
export function ProblemList({ compact = false }: { compact?: boolean }) {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLeetCodeProblems(studentId);
  const timer = useStudentStore((s) => s.leetcodeTimer);
  const startTimer = useStudentStore((s) => s.startLeetcodeTimer);
  const [pushedIds, setPushedIds] = useState<Set<string>>(new Set());

  if (isLoading) {
    return (
      <table className="lc-table">
        <tbody>
          <tr>
            <th>Problem</th>
            <th>Difficulty</th>
            <th>Status</th>
          </tr>
          {Array.from({ length: compact ? 2 : 4 }).map((_, i) => (
            <tr key={i}>
              <td colSpan={3}>
                <div className="skel skel-line" style={{ height: 16 }} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  const usingDemoData = (error || !data) && DEMO_MODE;
  const problemsSource = data ?? (usingDemoData ? DEMO_LEETCODE_PROBLEMS : null);

  if (!problemsSource) {
    return (
      <StateBlock
        variant="not-connected"
        tag="Not connected yet"
        message="LeetCode Tracker has no live backend yet — GET /leetcode/problems isn't built."
        ctaLabel="Retry"
        onCta={() => mutate()}
      />
    );
  }

  const problems = compact ? problemsSource.slice(0, 3) : problemsSource;

  if (problems.length === 0) {
    return <StateBlock message="No LeetCode problems queued yet." />;
  }

  return (
    <>
      {usingDemoData && (
        <span className="demo-badge" title="Real GET /leetcode/problems isn't connected — showing fixture data.">
          Demo data
        </span>
      )}
      <table className="lc-table">
        <tbody>
          <tr>
            <th>Problem</th>
            <th>Difficulty</th>
            <th>Status</th>
          </tr>
          {problems.map((p) => {
            const isRunning = timer?.problemId === p.id;
            const isPushed = pushedIds.has(p.id);
            return (
              <tr key={p.id}>
                <td>
                  <a href={p.link} target="_blank" rel="noreferrer">
                    {p.title}
                  </a>
                </td>
                <td>
                  <span className={`diff ${DIFF_CLASS[p.difficulty]}`}>
                    {p.difficulty[0].toUpperCase() + p.difficulty.slice(1)}
                  </span>
                </td>
                <td>
                  {isPushed ? (
                    <span className="mono" style={{ color: "var(--green)" }}>pushed ✓</span>
                  ) : isRunning ? (
                    <>
                      <TimerChip startedAt={timer!.startedAt} />{" "}
                      <PushConfirmButton
                        problemId={p.id}
                        onConfirmed={() => setPushedIds((s) => new Set(s).add(p.id))}
                      />
                    </>
                  ) : (
                    <button className="task-btn timer" onClick={() => startTimer(p.id)}>
                      ⏱ Start Timer
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
