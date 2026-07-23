"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useResumeBullets } from "@/lib/hooks";
import { StateBlock } from "@/components/state/StateBlock";
import { ResumeBulletRow } from "./ResumeBulletRow";

// generate_resume_bullet() exists in backend/logic/resume.py but is not
// mounted behind any route in backend/routes/ — no GET /resume/bullets to
// call yet. POST /resume/bullets/{id}/feedback IS live (backend/routes/
// feedback.py) and is wired for real via ResumeBulletRow.
export function ResumeCard({ compact = false }: { compact?: boolean }) {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useResumeBullets(studentId);

  if (isLoading) {
    return (
      <div className="resume-card">
        <div className="skel skel-line" style={{ height: 14, marginBottom: 8 }} />
        <div className="skel skel-line w-60" style={{ height: 14 }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <StateBlock
        variant="not-connected"
        tag="Not connected yet"
        message="Resume bullet generation has no live route yet — generate_resume_bullet() exists in the backend but isn't mounted behind GET /resume/bullets."
        ctaLabel="Retry"
        onCta={() => mutate()}
      />
    );
  }

  const bullets = compact ? data.slice(0, 1) : data;

  if (bullets.length === 0) {
    return <StateBlock message="No resume bullets yet — complete a module or project to generate one." />;
  }

  return (
    <>
      {bullets.map((b) => (
        <ResumeBulletRow key={b.id} bullet={b} />
      ))}
    </>
  );
}
