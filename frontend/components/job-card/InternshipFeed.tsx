"use client";

import { useStudentStore } from "@/lib/store-provider";
import { useJobs } from "@/lib/hooks";
import { StateBlock } from "@/components/state/StateBlock";
import { JobCard } from "./JobCard";

// GET /jobs is documented but not mounted in backend/routes/ yet — real
// typed hook, honest "not connected" state until the connector lands.
export function InternshipFeed({ compact = false }: { compact?: boolean }) {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useJobs(studentId);

  if (isLoading) {
    return (
      <>
        {Array.from({ length: compact ? 1 : 3 }).map((_, i) => (
          <div className="job-card" key={i}>
            <div className="skel skel-line w-60" style={{ height: 14, marginBottom: 8 }} />
            <div className="skel skel-line w-40" style={{ height: 11 }} />
          </div>
        ))}
      </>
    );
  }

  if (error || !data) {
    return (
      <StateBlock
        variant="not-connected"
        tag="Not connected yet"
        message="Internship Feed has no live backend yet — GET /jobs isn't built."
        ctaLabel="Retry"
        onCta={() => mutate()}
      />
    );
  }

  const jobs = compact ? data.slice(0, 2) : data;

  if (jobs.length === 0) {
    return <StateBlock message="No matching internships right now — check back after your next roadmap update." />;
  }

  return (
    <>
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </>
  );
}
