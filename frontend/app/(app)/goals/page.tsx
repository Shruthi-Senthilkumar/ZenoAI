"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useStudentStore } from "@/lib/store-provider";
import { useIntakeProfile, useResumeBullets, useGithubStatus } from "@/lib/hooks";
import { StateBlock } from "@/components/state/StateBlock";
import { ResumeBulletRow } from "@/components/resume-card/ResumeBulletRow";

// Goal & resume progress — the natural home for what /intake collects
// (target role, weekly hours) and what accumulates afterward (resume
// bullets), plus a readiness tie-in.
//
// Both GET /intake/profile and GET /resume/bullets are real, live
// routes now (backend/routes/intake_profile.py, resume_bullets.py) —
// this page previously showed a hardcoded "not connected yet" state
// for both while those routes didn't exist. What each section actually
// shows now:
//
//  - Target Role: a 404 from /intake/profile is a normal, expected
//    state meaning "hasn't completed intake yet" (backend checks a
//    real intake_completed_at timestamp, not just whether the row
//    exists — every seeded student already has non-null target_role/
//    weekly_hours defaults, so a null-check on those alone would
//    incorrectly claim a captured profile for someone who never did
//    intake). useIntakeProfile treats that 404 as data:null rather
//    than an SWR error, so this renders the empty-state prompt, not a
//    generic error block. A genuine fetch failure still surfaces via
//    profileError and gets a real retry affordance.
//  - Resume-in-progress: /resume/bullets always returns 200 with an
//    empty array for a student with no bullets yet — never 404. So
//    bulletsError here now means a real failure, not "nothing yet";
//    the empty-list case is handled separately from the error case.
//  - There's still no PATCH/PUT to edit an already-captured target
//    role — retaking intake is still the only way to change it. That
//    part of the original gap is real and unchanged.
//
// Career readiness IS real — it's pulled from the shared store rather
// than re-fetched, populated by whichever of Today/Dashboard loaded
// first this session (see their setReadiness calls).
//
// GitHub connect: real OAuth flow, backend/routes/auth.py. Full
// server-side redirect, not a fetch — the button is a plain <a>, GitHub's
// authorize page needs a real top-level navigation, not an XHR.
export default function GoalsPage() {
  const studentId = useStudentStore((s) => s.studentId);
  const readiness = useStudentStore((s) => s.readiness);
  const searchParams = useSearchParams();
  const githubParam = searchParams.get("github");

  const {
    data: profile,
    error: profileError,
    isLoading: profileLoading,
  } = useIntakeProfile(studentId);
  const {
    data: bullets,
    error: bulletsError,
    isLoading: bulletsLoading,
    mutate: mutateBullets,
  } = useResumeBullets(studentId);
  const {
    data: githubStatus,
    isLoading: githubLoading,
  } = useGithubStatus(studentId);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const authorizeUrl = `${apiBaseUrl}/auth/github/authorize?student_id=${studentId}`;

  return (
    <section className="tab-panel active" id="tab-goals">
      <div className="section-label">Goal &amp; resume progress</div>

      {githubParam === "connected" && (
        <div className="notif-banner milestone" style={{ marginBottom: 16 }}>
          GitHub connected — commit activity will feed your career readiness.
        </div>
      )}
      {githubParam === "exchange_failed" && (
        <div className="notif-banner offline" style={{ marginBottom: 16 }}>
          GitHub connection failed — please try again.
        </div>
      )}
      {githubParam === "state_mismatch" && (
        <div className="notif-banner offline" style={{ marginBottom: 16 }}>
          That connection link expired — please try again.
        </div>
      )}

      <div className="panel career" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <h3>GitHub</h3>
          <span className="chip-tag">career evidence</span>
        </div>

        {githubLoading ? (
          <div className="skel skel-line w-60" style={{ height: 16 }} />
        ) : githubStatus?.connected ? (
          <>
            <div className="gauge">
              <b>Connected</b>
            </div>
            <div className="confidence">
              {githubStatus.github_username ? `@${githubStatus.github_username}` : "Account linked"}
            </div>
          </>
        ) : (
          <>
            <p className="lms-muted" style={{ marginBottom: 10 }}>
              Connect GitHub to feed real commit activity into your career readiness and struggle-detector signals.
            </p>
            <a href={authorizeUrl} className="task-btn" style={{ display: "inline-block" }}>
              Connect GitHub
            </a>
          </>
        )}
      </div>

      <div className="panel career" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <h3>Target Role</h3>
          <span className="chip-tag">from Adaptive Intake</span>
        </div>

	{profileLoading ? (
          <div className="skel skel-line w-60" style={{ height: 16 }} />
        ) : profileError ? (
          <StateBlock
            variant="error"
            message="Couldn't load your goal — check your connection and try again."
            ctaLabel="Retry"
            onCta={() => window.location.reload()}
          />
        ) : profile ? (
          <>
            <div className="gauge">
              <b>{profile.targetRole}</b>
            </div>
            <div className="confidence">
              {profile.weeklyHours} hrs/week planned · {profile.timelineMonths}-month plan · {profile.educationLevel}
            </div>
            {Object.keys(profile.topicLevels).length > 0 && (
              <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
                {Object.entries(profile.topicLevels).map(([topic, level]) => (
                  <span key={topic} className="chip-tag" title="Evaluated from your diagnostic answer, not self-rated">
                    {topic}: {level}
                  </span>
                ))}
              </div>
            )}
          </>
        ) : (
          <p className="lms-muted">
            No goal set yet. <Link href="/intake">Complete intake</Link> to capture your target role and weekly
            hours.
          </p>
        )}
        <div className="subj-row" style={{ borderTop: "1px solid var(--line)", marginTop: 14, paddingTop: 14 }}>
          <span>Career Readiness</span>
          <span className="mono">
            {Math.round(readiness.career * 100)}% · confidence {readiness.confidence}
          </span>
        </div>

        {profile && (
          <p className="lms-muted" style={{ marginTop: 4 }}>
            Want to change your goal? Retaking <Link href="/intake">intake</Link> is the only way to update it right
            now — there's no direct edit yet.
          </p>
        )}
      </div>

      <div className="section-label">Resume in progress</div>

      {bulletsLoading && (
        <div className="resume-card">
          <div className="skel skel-line" style={{ height: 14, marginBottom: 8 }} />
          <div className="skel skel-line w-60" style={{ height: 14 }} />
        </div>
      )}

      {bulletsError && !bulletsLoading && (
        <StateBlock
          variant="error"
          message="Couldn't load your resume bullets — check your connection and try again."
          ctaLabel="Retry"
          onCta={() => mutateBullets()}
        />
      )}

      {bullets && bullets.length === 0 && !bulletsError && (
        <StateBlock message="No resume bullets yet — complete a module or project to generate one." />
      )}

      {bullets?.map((b) => (
        <ResumeBulletRow key={b.id} bullet={b} />
      ))}
    </section>
  );
}