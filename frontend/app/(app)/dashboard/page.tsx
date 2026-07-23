"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useStudentStore } from "@/lib/store-provider";
import { useDashboard } from "@/lib/hooks";
import { GaugeSkeleton } from "@/components/skeleton/GaugeSkeleton";
import { StateBlock } from "@/components/state/StateBlock";
import { ProblemList } from "@/components/leetcode/ProblemList";
import { InternshipFeed } from "@/components/job-card/InternshipFeed";
import { ResumeCard } from "@/components/resume-card/ResumeCard";
import type { Confidence } from "@/lib/types";

const CONFIDENCE_RANK: Record<Confidence, number> = { low: 0, medium: 1, high: 2 };

// Mirrors backend/logic/tasks.py's _combine_confidence: one confidence
// slot covers two separate readiness numbers, so it takes the weaker of
// the two rather than implying more certainty than the thinner-evidence
// side actually has.
function combineConfidence(a: Confidence, b: Confidence): Confidence {
  return CONFIDENCE_RANK[a] <= CONFIDENCE_RANK[b] ? a : b;
}

function averageTrend(subjects: Record<string, number[]>): number[] {
  const series = Object.values(subjects);
  const maxLen = series.reduce((m, s) => Math.max(m, s.length), 0);
  const out: number[] = [];
  for (let i = 0; i < maxLen; i++) {
    const vals = series.map((s) => s[i]).filter((v) => v !== undefined);
    if (vals.length) out.push(vals.reduce((a, b) => a + b, 0) / vals.length / 100);
  }
  return out;
}

export default function DashboardPage() {
  const router = useRouter();
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useDashboard(studentId);
  const streak = useStudentStore((s) => s.streak);
  const setStreak = useStudentStore((s) => s.setStreak);
  const setReadiness = useStudentStore((s) => s.setReadiness);

  // The topbar's streak chip reads store.streak, which is otherwise only
  // populated by Today's fetch — land here directly (bookmark, refresh)
  // and it would stay at its zero-value default. Dashboard's own response
  // carries a streak count too, so merge it in rather than leaving the
  // chip stale. academicDone/careerActive aren't in this response, so
  // they're left as whatever Today last set (or the default).
  useEffect(() => {
    if (data) setStreak({ ...streak, count: data.career.streak });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.career.streak]);

  // store.readiness otherwise only gets populated by Today's fetch. The
  // Goals page (item 5) needs career readiness without re-fetching
  // Dashboard's data itself, so push it into the shared store here too —
  // whichever of Today/Dashboard loads first in a session populates it.
  useEffect(() => {
    if (data) {
      setReadiness({
        academic: data.academic.readiness,
        career: data.career.readiness,
        confidence: combineConfidence(data.academic.confidence, data.career.confidence),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.academic.readiness, data?.career.readiness, data?.academic.confidence, data?.career.confidence]);

  if (isLoading) {
    return (
      <section className="tab-panel active" id="tab-dashboard">
        <div className="section-label">Dual readiness — never blended</div>
        <div className="panel-grid">
          <div className="panel academic">
            <GaugeSkeleton />
          </div>
          <div className="panel career">
            <GaugeSkeleton />
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="tab-panel active" id="tab-dashboard">
        <div className="section-label">Dual readiness — never blended</div>
        <StateBlock
          variant="error"
          message="Couldn't load your dashboard."
          ctaLabel="Retry"
          onCta={() => mutate()}
        />
      </section>
    );
  }

  const academicTrend = averageTrend(data.academic.subjects);
  const subjectRows = Object.entries(data.academic.subjects);

  return (
    <section className="tab-panel active" id="tab-dashboard">
      <div className="section-label">Dual readiness — never blended</div>

      <div className="panel-grid">
        <div className="panel academic">
          <div className="panel-head">
            <h3>Academic</h3>
            <span className="chip-tag">via LMS Connector</span>
          </div>
          <div className="gauge">
            <b>{Math.round(data.academic.readiness * 100)}%</b>
            <span>Readiness</span>
          </div>
          <div className="confidence">Confidence: {data.academic.confidence}</div>

          {academicTrend.length === 0 ? (
            <StateBlock
              message="Not enough evidence yet to chart a trend."
              ctaLabel="View your roadmap"
              onCta={() => {
                router.push("/roadmap");
              }}
            />
          ) : (
            <div className="mini-bars">
              {academicTrend.map((v, i) => (
                <div className="bar" key={i} style={{ ["--v" as any]: v }}></div>
              ))}
            </div>
          )}

          {subjectRows.length === 0 ? (
            <p className="lms-muted">No subjects tracked yet.</p>
          ) : (
            subjectRows.map(([subject, scores]) => {
              const latest = scores[scores.length - 1];
              const prev = scores[scores.length - 2];
              const trendClass = prev === undefined ? "mono" : latest >= prev ? "trend-up mono" : "trend-down mono";
              const arrow = prev === undefined ? "" : latest >= prev ? " ↑" : " ↓";
              return (
                <div className="subj-row" key={subject}>
                  <span>{subject}</span>
                  <span className={trendClass}>
                    {latest}%{arrow}
                  </span>
                </div>
              );
            })
          )}
        </div>

        <div className="panel career">
          <div className="panel-head">
            <h3>Career</h3>
            <span className="chip-tag">GitHub + LeetCode</span>
          </div>
          <div className="gauge">
            <b>{Math.round(data.career.readiness * 100)}%</b>
            <span>Readiness</span>
          </div>
          <div className="confidence">Confidence: {data.career.confidence}</div>

          {data.career.activity_trend.length === 0 ? (
            <StateBlock
              message="Not enough evidence yet to chart a trend."
              ctaLabel="View your roadmap"
              onCta={() => {
                router.push("/roadmap");
              }}
            />
          ) : (
            <div className="mini-bars">
              {data.career.activity_trend.map((v, i) => (
                <div className="bar" key={i} style={{ ["--v" as any]: v }}></div>
              ))}
            </div>
          )}

          <div className="section-label" style={{ margin: "16px 0 4px" }}>
            LeetCode Tracker
          </div>
          <ProblemList compact />

          <div className="section-label" style={{ margin: "16px 0 4px" }}>
            Internship Feed
          </div>
          <InternshipFeed compact />

          <div className="section-label" style={{ margin: "16px 0 4px" }}>
            Resume Bullet Review
          </div>
          <ResumeCard compact />
        </div>
      </div>
    </section>
  );
}
