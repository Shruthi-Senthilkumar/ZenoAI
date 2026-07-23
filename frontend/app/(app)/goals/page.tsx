"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useStudentStore } from "@/lib/store-provider";
import { useIntakeProfile, useResumeBullets, useGithubStatus } from "@/lib/hooks";
import { StateBlock } from "@/components/state/StateBlock";
import { ResumeBulletRow } from "@/components/resume-card/ResumeBulletRow";

// New page (item 5) — the natural home for what /intake collects (target
// role, weekly hours) and what accumulates afterward (resume bullets),
// plus a readiness tie-in. Two of its three original sections have no
// live backend to call yet:
//
//  - Goal summary: backend/logic/intake.py only stores target role/weekly
//    hours as free text inside its internal IntakeState.answers list —
//    nothing in backend/routes/ exposes a GET that returns them back out
//    in structured form, and there's no update endpoint either. So this
//    is "not connected" (can't even read it back), not "no goal set yet"
//    — those are different claims, and only the honest one is made here.
//    No fake edit flow is built for the same reason.
//  - Resume-in-progress: same GET /resume/bullets gap as Dashboard's
//    ResumeCard — reuses the exact same useResumeBullets hook per item 5's
//    instruction to build the fetch hook once and reuse it in both places.
//
// Career readiness IS real — it's pulled from the shared store rather
// than re-fetched, populated by whichever of Today/Dashboard loaded
// first this session (see their setReadiness calls).
//
// GitHub connect (new): real OAuth flow, backend/routes/auth.py. Full
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
    mutate: mutateProfile,
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
        <div className="toast" style={{ position: "static", marginBottom: 16 }}>
          GitHub connected — commit activity will feed your career readiness.
        </div>
      )}
      {githubParam === "exchange_failed" && (
        <div className="toast" style={{ position: "static", marginBottom: 16 }}>
          GitHub connection failed — please try again.
        </div>
      )}
      {githubParam === "state_mismatch" && (
        <div className="toast" style={{ position: "static", marginBottom: 16 }}>
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
        ) : profileError || !profile ? (
          <StateBlock
            variant="not-connected"
            tag="Not connected yet"
            message="No endpoint exposes your captured intake profile yet, and there's no update endpoint either — editing isn't wired for the same reason. Retake intake to (re)capture your goal once this connects."
            ctaLabel="Retry"
            onCta={() => mutateProfile()}
          />
        ) : (
          <>
            <div className="gauge">
              <b>{profile.targetRole}</b>
            </div>
            <div className="confidence">{profile.weeklyHours} hrs/week planned</div>
          </>
        )}

        <div className="subj-row" style={{ borderTop: "1px solid var(--line)", marginTop: 14, paddingTop: 14 }}>
          <span>Career Readiness</span>
          <span className="mono">
            {Math.round(readiness.career * 100)}% · confidence {readiness.confidence}
          </span>
        </div>

        <p className="lms-muted" style={{ marginTop: 4 }}>
          Haven&apos;t set a goal yet? <Link href="/intake">Complete intake</Link> to get started.
        </p>
      </div>

      <div className="section-label">Resume in progress</div>

      {bulletsLoading && (
        <div className="resume-card">
          <div className="skel skel-line" style={{ height: 14, marginBottom: 8 }} />
          <div className="skel skel-line w-60" style={{ height: 14 }} />
        </div>
      )}

      {(bulletsError || !bullets) && !bulletsLoading && (
        <StateBlock
          variant="not-connected"
          tag="Not connected yet"
          message="Resume bullet generation has no live route yet — generate_resume_bullet() exists in the backend but isn't mounted behind GET /resume/bullets."
          ctaLabel="Retry"
          onCta={() => mutateBullets()}
        />
      )}

      {bullets && bullets.length === 0 && (
        <StateBlock message="No resume bullets yet — complete a module or project to generate one." />
      )}

      {bullets?.map((b) => (
        <ResumeBulletRow key={b.id} bullet={b} />
      ))}
    </section>
  );
}