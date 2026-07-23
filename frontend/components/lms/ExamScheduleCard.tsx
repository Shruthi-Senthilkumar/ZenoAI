"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsExamSchedule } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

export function ExamScheduleCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsExamSchedule(studentId);

  return (
    <LmsCardShell
      title="Exam Schedule"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={!!data && data.length === 0}
      notConnectedMessage="Exam schedule connector isn't live yet — no /lms/exam-schedule route exists."
      emptyMessage="No exams on the schedule yet."
      onRetry={() => mutate()}
    >
      {data?.map((e, i) => (
        <div className="lms-row" key={i}>
          <span>{e.subject}</span>
          <span className="lms-muted">
            {e.date} · {e.time}
          </span>
        </div>
      ))}
    </LmsCardShell>
  );
}
