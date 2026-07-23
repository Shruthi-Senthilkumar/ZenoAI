"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsProgrammingProgress } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

export function ProgrammingProgressCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsProgrammingProgress(studentId);

  return (
    <LmsCardShell
      title="Programming Progress"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={!!data && data.length === 0}
      notConnectedMessage="Programming progress connector isn't live yet — no /lms/programming-progress route exists."
      emptyMessage="No programming modules on record yet."
      onRetry={() => mutate()}
    >
      {data?.map((p, i) => (
        <div className="lms-row" key={i}>
          <span>{p.language}</span>
          <span className="lms-muted">
            {p.modulesCompleted}/{p.modulesTotal} modules
          </span>
        </div>
      ))}
    </LmsCardShell>
  );
}
