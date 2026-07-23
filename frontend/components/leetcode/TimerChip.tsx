"use client";

import { useEffect, useState } from "react";

function formatElapsed(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const mm = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const ss = String(totalSeconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

// Presentational only — startedAt lives in the Zustand store (see
// startLeetcodeTimer/stopLeetcodeTimer in lib/store.ts) so the timer
// survives navigating away from the tracker; this component just ticks a
// local re-render every second to keep the display live.
export function TimerChip({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  return <span className="timer-chip">⏱ {formatElapsed(now - startedAt)} running</span>;
}
