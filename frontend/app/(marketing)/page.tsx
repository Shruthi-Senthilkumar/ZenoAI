"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LandingPage() {
  const router = useRouter();
  const [showLogin, setShowLogin] = useState(false);
  const revealRefs = useRef<HTMLElement[]>([]);

  function openLogin(e: React.MouseEvent) {
    e.preventDefault();
    setShowLogin(true);
  }

  function enterApp() {
    router.push("/today");
  }

  function handleLoginSubmit(e: React.FormEvent) {
    e.preventDefault();
    enterApp();
  }

  useEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const els = revealRefs.current;
    if (reduceMotion) {
      els.forEach((el) => el.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  const addReveal = (el: HTMLElement | null) => {
    if (el && !revealRefs.current.includes(el)) revealRefs.current.push(el);
  };

  return (
    <>
      {/* ================= LOGIN GATE ================= */}
      <div id="loginScreen" className={showLogin ? "show" : ""}>
        <div className="login-orb"></div>
        <div className="login-orb b"></div>
        <div className="login-card">
          <div className="brand">
            <span className="dot"></span> ZENO AI
          </div>
          <h2>Welcome back</h2>
          <p className="sub">Log in to see your roadmap, streak, and readiness.</p>
          <form id="loginForm" onSubmit={handleLoginSubmit}>
            <div className="field">
              <label htmlFor="loginEmail">Email</label>
              <input
                id="loginEmail"
                type="email"
                placeholder="you@college.edu"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="loginPass">Password</label>
              <input
                id="loginPass"
                type="password"
                placeholder="••••••••"
                required
              />
            </div>
            <button type="submit" className="login-btn">
              Log in
            </button>
          </form>
          <div className="login-divider">or</div>
          <button
            className="btn-secondary"
            id="guestBtn"
            style={{ width: "100%" }}
            onClick={enterApp}
          >
            Continue as guest
          </button>
          <p className="login-alt">
            New here?{" "}
            <a href="/intake" className="intake-link" onClick={openLogin}>
              Start your intake →
            </a>
          </p>
        </div>
      </div>

      <div id="site">
        {/* ================= NAV ================= */}
        <nav className="nav">
          <div className="brand">
            <span className="dot"></span> ZENO AI
          </div>
          <div className="nav-links">
            <a href="#loop">How it works</a>
            <a href="#features">Product</a>
            <Link href="/today">App</Link>
          </div>
          <a href="/intake" className="intake-link" onClick={openLogin}>
            <button className="nav-cta">Launch Zeno</button>
          </a>
        </nav>

        {/* ================= HERO ================= */}
        <header className="hero">
          <div className="hero-pill">
            <span className="new">NEW</span> Dual readiness, never blended
            into one score
          </div>
          <div className="eyebrow">
            Academic + career mentor · one roadmap, two honest scores
          </div>
          <h1>
            One mentor. <span className="ac">Two scores</span> that never{" "}
            <span className="cr">lie to each other</span>.
          </h1>
          <p className="sub">
            ZenoAI reads your LMS and your GitHub, builds one
            prerequisite-aware roadmap, and tells you — honestly — where you
            stand in class and where you stand in the job market. Never
            blended into one misleading number.
          </p>
          <div className="hero-ctas">
            <a href="/intake" className="intake-link" onClick={openLogin}>
              <button className="btn-primary">Start your intake →</button>
            </a>
          </div>
          <div className="hero-features">
            <div className="hero-feat">
              <span className="ic">🎓</span>LMS Connector
            </div>
            <div className="hero-feat">
              <span className="ic">🐙</span>GitHub + LeetCode sync
            </div>
            <div className="hero-feat">
              <span className="ic">🧭</span>Prerequisite-aware DAG
            </div>
            <div className="hero-feat">
              <span className="ic">💬</span>Mentor AI chat
            </div>
          </div>
        </header>

        <div className="wrap">
          <div className="impact reveal" ref={addReveal}>
            <div className="impact-cell ac">
              <b>2</b>
              <span>Readiness scores, never blended</span>
            </div>
            <div className="impact-cell cr">
              <b>~30</b>
              <span>Prerequisite DAG nodes</span>
            </div>
            <div className="impact-cell">
              <b>1</b>
              <span>Merged task list, not two tabs</span>
            </div>
            <div className="impact-cell">
              <b>0</b>
              <span>Times you're called "behind"</span>
            </div>
          </div>
        </div>

        {/* ================= THE LOOP ================= */}
        <section className="section" id="loop">
          <div className="wrap">
            <div className="section-head reveal" ref={addReveal}>
              <div className="eyebrow">How it works</div>
              <h2>The loop, run every day</h2>
              <p>
                Same four steps whether you're closing a gap in DBMS or a
                gap in your GitHub history — one engine, two goal types.
              </p>
            </div>
            <div className="loop-grid reveal" ref={addReveal}>
              <div className="loop-step">
                <span className="num">01</span>
                <h3>Connect</h3>
                <p>
                  LMS Connector reads your quiz scores, assignments, and
                  exam schedule. GitHub OAuth is opt-in — never a gate on
                  using the rest of the product.
                </p>
                <span className="tag both">Both</span>
              </div>
              <div className="loop-step">
                <span className="num">02</span>
                <h3>Diagnose</h3>
                <p>
                  A branching intake asks one question at a time and stops
                  the moment it's confident in your level — known material
                  is never re-taught.
                </p>
                <span className="tag both">Both</span>
              </div>
              <div className="loop-step">
                <span className="num">03</span>
                <h3>Plan</h3>
                <p>
                  One DAG walk, two directions: academic items
                  backward-planned from your exams, career items
                  forward-planned from your target role.
                </p>
                <span className="tag both">Both</span>
              </div>
              <div className="loop-step">
                <span className="num">04</span>
                <h3>Grow</h3>
                <p>
                  A merged daily list, a dual-gated streak, and a mentor
                  that talks about your dips like a coach — never a
                  verdict.
                </p>
                <span className="tag both">Both</span>
              </div>
            </div>
          </div>
        </section>

        {/* ================= FEATURES ================= */}
        <section className="section tight" id="features">
          <div className="wrap">
            <div className="section-head reveal" ref={addReveal}>
              <div className="eyebrow">Product</div>
              <h2>Everything reads in one of two colors</h2>
              <p>
                Indigo is academic. Amber is career. The split is never
                explained with a legend — it becomes legible by repetition
                across every card, chart, and badge.
              </p>
            </div>
            <div className="feat-grid reveal" ref={addReveal}>
              <div className="feat-card ac">
                <span className="goal-badge academic">Academic</span>
                <h3>LMS Connector</h3>
                <p>
                  A swappable connector layer — mock JSON today, your real
                  Moodle install tomorrow, with zero change to roadmap,
                  scoring, or struggle-detection logic.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Skill / Subject DAG</h3>
                <p>
                  A hand-authored prerequisite graph. A topic is never
                  scheduled before what it depends on — accuracy that
                  doesn't rely on a model guessing.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Adaptive Intake</h3>
                <p>
                  Conversational, one question at a time. Confidence in
                  your level is tracked live — no wasted questions on
                  things you already know.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Roadmap Generator</h3>
                <p>
                  Level-aware, not template-based. The DAG is walked from
                  your first real gap — never from basics, no matter who
                  you are.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Daily Micro-Tests</h3>
                <p>
                  3–5 sharp questions per completed topic. Pass or fail
                  corrects your skill vector and feeds the streak — on the
                  spot, not next week.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Dual-Gated Streak</h3>
                <p>
                  Increments only when an academic task <em>and</em> career
                  activity both land the same day. Logging in alone never
                  counts.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Struggle-Detector</h3>
                <p>
                  Flags a dip as an offer, never a verdict. "Not actually
                  stuck" sits right next to "yes, help me" — same size,
                  same weight.
                </p>
              </div>
              <div className="feat-card">
                <span className="goal-badge both">Both</span>
                <h3>Dual Readiness Score</h3>
                <p>
                  Academic vs. exam syllabus. Career vs. your target role.
                  Computed separately, shown separately — never blended
                  into one misleading number.
                </p>
              </div>
              <div className="feat-card cr">
                <span className="goal-badge career">Career</span>
                <h3>LeetCode Tracker + GitHub</h3>
                <p>
                  An in-app timer, no browser extension. Push your
                  solution, the existing GitHub poller parses the result —
                  one ingestion path, not two.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ================= FINAL CTA ================= */}
        <section className="section tight">
          <div className="wrap">
            <div className="final-cta reveal" ref={addReveal}>
              <h2>Your roadmap starts with one question.</h2>
              <p>
                No signup wall, no GitHub prompt on question one — just the
                intake, and a preview of your first gap.
              </p>
              <a href="/intake" className="intake-link" onClick={openLogin}>
                <button className="btn-primary">Start your intake →</button>
              </a>
            </div>
          </div>
        </section>

        {/* ================= FOOTER ================= */}
        <footer>
          <div className="wrap">
            <div className="foot-grid">
              <div className="foot-brand">
                <div className="brand">
                  <span className="dot"></span> ZENO AI
                </div>
                <p>
                  One prerequisite-aware roadmap. Two honest readiness
                  scores. Never blended, never a verdict.
                </p>
              </div>
              <div>
                <h5>Product</h5>
                <ul>
                  <li>
                    <a href="#loop">How it works</a>
                  </li>
                  <li>
                    <a href="#features">Features</a>
                  </li>
                  <li>
                    <Link href="/today">App</Link>
                  </li>
                </ul>
              </div>
              <div>
                <h5>Get started</h5>
                <ul>
                  <li>
                    <a href="/intake" className="intake-link" onClick={openLogin}>
                      Start intake
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h5>Company</h5>
                <ul>
                  <li>
                    <a href="#">About</a>
                  </li>
                  <li>
                    <a href="#">Privacy</a>
                  </li>
                </ul>
              </div>
            </div>
            <div className="foot-bottom">
              <span>© 2026 ZenoAI. Built for a 24-hour hackathon.</span>
              <span>
                Academic <span style={{ color: "var(--indigo)" }}>■</span> ·
                Career <span style={{ color: "var(--amber)" }}>■</span>
              </span>
            </div>
          </div>
        </footer>
      </div>
      {/* /#site */}
    </>
  );
}
