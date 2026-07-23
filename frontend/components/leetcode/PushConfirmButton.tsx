"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useStudentStore } from "@/lib/store-provider";

interface PushConfirmButtonProps {
  problemId: string;
  onConfirmed: () => void; // only called on a genuine 2xx — never faked
}

// Always attempts the real POST /leetcode/{id}/push-confirm first, even
// for a demo-fixture problem — that route doesn't exist on the backend
// yet, so this will fail today, and the failure is shown honestly rather
// than pretending the push was recorded.
export function PushConfirmButton({ problemId, onConfirmed }: PushConfirmButtonProps) {
  const studentId = useStudentStore((s) => s.studentId);
  const stopTimer = useStudentStore((s) => s.stopLeetcodeTimer);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function onClick() {
    stopTimer(); // stopping the clock is a client action, independent of backend confirmation
    setPending(true);
    setError(null);
    api
      .post(`/leetcode/${problemId}/push-confirm`, { student_id: studentId })
      .then(() => onConfirmed())
      .catch(() => setError("Not connected yet — push-confirm has no live backend route."))
      .finally(() => setPending(false));
  }

  if (error) {
    return <span className="lms-muted">{error}</span>;
  }

  return (
    <button className="task-btn timer" disabled={pending} onClick={onClick}>
      {pending ? "Confirming…" : "I've pushed my solution"}
    </button>
  );
}
