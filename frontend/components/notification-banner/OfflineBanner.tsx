"use client";

import { useOnlineStatus } from "./useOnlineStatus";

// Always top priority when active — no server banner renders alongside this
// one (NotificationBanner suppresses itself while offline).
export function OfflineBanner() {
  const online = useOnlineStatus();
  if (online) return null;

  return (
    <div className="notif-banner offline">
      <p>📡 You&apos;re offline — some data may be out of date.</p>
    </div>
  );
}
