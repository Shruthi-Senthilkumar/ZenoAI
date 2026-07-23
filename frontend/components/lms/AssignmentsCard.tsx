"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsAssignments } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

export function AssignmentsCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsAssignments(studentId);

  return (
    <LmsCardShell
      title="Assignments"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={!!data && data.length === 0}
      notConnectedMessage="Assignments connector isn't live yet — no /lms/assignments route exists."
      emptyMessage="No assignments on record yet."
      onRetry={() => mutate()}
    >
      {data?.map((a, i) => (
        <div className="lms-row" key={i}>
          <span>
            {a.subject} · {a.title}
          </span>
          <span className="lms-muted">{a.submitted ? "submitted" : `due ${a.dueDate}`}</span>
        </div>
      ))}
    </LmsCardShell>
  );
}
