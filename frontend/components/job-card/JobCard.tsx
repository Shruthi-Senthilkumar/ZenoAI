"use client";

import { useState } from "react";
import type { JobListing } from "@/lib/types";

export function JobCard({ job }: { job: JobListing }) {
  const [applyNote, setApplyNote] = useState(false);

  return (
    <div className="job-card">
      <div className="row">
        <p>
          {job.title} — {job.company}
        </p>
        <span className="match">{job.match_pct}% match</span>
      </div>
      {job.missing_skills.length > 0 && (
        <div className="missing">Missing: {job.missing_skills.join(", ")}</div>
      )}
      {applyNote ? (
        <div className="missing">Apply flow isn&apos;t connected yet.</div>
      ) : (
        <button className="task-btn" style={{ marginTop: 8 }} onClick={() => setApplyNote(true)}>
          Apply
        </button>
      )}
    </div>
  );
}