"use client";

import type { ReactNode } from "react";
import { StateBlock } from "@/components/state/StateBlock";

interface LmsCardShellProps {
  title: string;
  isLoading: boolean;
  error: boolean;
  empty: boolean;
  notConnectedMessage: string;
  emptyMessage: string;
  onRetry: () => void;
  children: ReactNode;
}

// Shared chrome only — every card owns its own SWR call, so a failure in
// one never blanks the other six (no global error boundary here).
export function LmsCardShell({
  title,
  isLoading,
  error,
  empty,
  notConnectedMessage,
  emptyMessage,
  onRetry,
  children,
}: LmsCardShellProps) {
  return (
    <div className="lms-card">
      <div className="lms-card-head">
        <h3>{title}</h3>
      </div>
      {isLoading ? (
        <>
          <div className="skel skel-line w-60" style={{ height: 14, marginBottom: 8 }} />
          <div className="skel skel-line w-40" style={{ height: 14 }} />
        </>
      ) : error ? (
        <StateBlock
          variant="not-connected"
          tag="Not connected yet"
          message={notConnectedMessage}
          ctaLabel="Retry"
          onCta={onRetry}
        />
      ) : empty ? (
        <StateBlock message={emptyMessage} />
      ) : (
        children
      )}
    </div>
  );
}
