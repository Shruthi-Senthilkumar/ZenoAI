"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useLmsStudentProfile } from "@/lib/hooks";
import { LmsCardShell } from "./LmsCardShell";

// get_student_profile() — Integration Spec's connector method 1/6. No
// /lms/* route family exists in backend/routes/ yet (Subhiksha's unbuilt
// scope) — this hits the documented path and shows "not connected" until
// it does.
export function StudentProfileCard() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useLmsStudentProfile(studentId);

  return (
    <LmsCardShell
      title="Student Profile"
      isLoading={isLoading}
      error={!!error || (!isLoading && !data)}
      empty={false}
      notConnectedMessage="LMS profile connector isn't live yet — get_student_profile() has no route."
      emptyMessage=""
      onRetry={() => mutate()}
    >
      {data && (
        <>
          <div className="lms-row">
            <span>Name</span>
            <span className="lms-muted">{data.name}</span>
          </div>
          <div className="lms-row">
            <span>Program</span>
            <span className="lms-muted">{data.program}</span>
          </div>
          <div className="lms-row">
            <span>Year</span>
            <span className="lms-muted">{data.year}</span>
          </div>
          <div className="lms-row">
            <span>Roll Number</span>
            <span className="lms-muted">{data.rollNumber}</span>
          </div>
        </>
      )}
    </LmsCardShell>
  );
}
