"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsQuizScores } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

export function QuizScoresCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsQuizScores(studentId);

  return (
    <LmsCardShell
      title="Quiz Scores"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={!!data && data.length === 0}
      notConnectedMessage="Quiz score connector isn't live yet — no /lms/quiz-scores route exists."
      emptyMessage="No quiz scores on record yet."
      onRetry={() => mutate()}
    >
      {data?.map((q, i) => (
        <div className="lms-row" key={i}>
          <span>
            {q.subject} · {q.quiz}
          </span>
          <span className="lms-muted">
            {q.score}/{q.maxScore}
          </span>
        </div>
      ))}
    </LmsCardShell>
  );
}
