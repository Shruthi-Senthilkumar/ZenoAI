"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { StudentStoreProvider, useStudentStore } from "../../lib/store-provider";
import { NotificationBanner } from "../../components/notification-banner/NotificationBanner";
import { OfflineBanner } from "../../components/notification-banner/OfflineBanner";
import "../../styles/app-shell.css";

const TABS = [
  { href: "/today", label: "Today", icon: "▣" },
  { href: "/roadmap", label: "Roadmap", icon: "◷" },
  { href: "/dashboard", label: "Dashboard", icon: "▤" },
  { href: "/goals", label: "Goals", icon: "◎" },
  { href: "/lms", label: "LMS", icon: "🎓" },
  { href: "/leetcode", label: "LeetCode", icon: "⌘" },
  { href: "/chat", label: "Chat", icon: "◐" },
];

// No auth/session layer exists anywhere in this repo — there is no login
// flow to source a real studentId from. This mirrors the one fixture key
// ("student-1") the backend's in-memory stub DBs actually have data under
// (see backend/routes/dashboard.py, backend/logic/streak.py). Replacing
// this with a real session's studentId is the real missing piece, flagged
// in the final report, not papered over here.
const PLACEHOLDER_STUDENT_ID = "student-1";

function AppShellInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const studentId = useStudentStore((s) => s.studentId);
  const setStudentId = useStudentStore((s) => s.setStudentId);
  const streak = useStudentStore((s) => s.streak);

  useEffect(() => {
    if (!studentId) setStudentId(PLACEHOLDER_STUDENT_ID);
  }, [studentId, setStudentId]);

  const activeTab = TABS.find((t) => pathname?.startsWith(t.href));
  const title = activeTab ? activeTab.label : "Today";

  return (
    <div className="app">
      <nav className="rail">
        <div className="rail-brand">
          <span className="dot"></span> ZENO AI
        </div>
        <Link className="rail-back" href="/">
          ← zenoai.com
        </Link>
        {TABS.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={`rail-tab${pathname?.startsWith(tab.href) ? " active" : ""}`}
          >
            <span className="ic">{tab.icon}</span> {tab.label}
          </Link>
        ))}
        <Link href="/intake" className="rail-tab" style={{ opacity: 0.85 }}>
          <span className="ic">✎</span> Retake Intake
        </Link>
        <div className="rail-foot">
          Academic <span style={{ color: "var(--indigo)" }}>■</span> ·
          Career <span style={{ color: "var(--amber)" }}>■</span>
        </div>
      </nav>

      <div className="main">
        <div className="topbar">
          <h1 id="topbarTitle">{title}</h1>
          <div className="streak-chip">🔥 {streak.count}-day streak</div>
        </div>

        <div className="content">
          <OfflineBanner />
          <NotificationBanner />
          {children}
        </div>
      </div>
    </div>
  );
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <StudentStoreProvider>
      <AppShellInner>{children}</AppShellInner>
    </StudentStoreProvider>
  );
}
