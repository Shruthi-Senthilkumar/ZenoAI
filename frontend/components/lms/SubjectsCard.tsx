"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsSubjects } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

export function SubjectsCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsSubjects(studentId);

  return (
    <LmsCardShell
      title="Subjects"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={!!data && data.length === 0}
      notConnectedMessage="Subjects connector isn't live yet — no /lms/subjects route exists."
      emptyMessage="No subjects on record yet."
      onRetry={() => mutate()}
    >
      {data?.map((subject) => (
        <div className="lms-row" key={subject.code}>
          <span>{subject.name}</span>
          <span className="lms-muted">{subject.instructor}</span>
        </div>
      ))}
    </LmsCardShell>
  );
}
