"use client";

import { useState } from "react";
import { useStudentStore } from "@/lib/store-provider";
import { useNotifications } from "@/lib/hooks";
import { useOnlineStatus } from "./useOnlineStatus";

// Priority ordering and "max one banner" are enforced server-side
// (backend/logic/notifications.py) — this just renders whatever single
// banner object (or null) comes back, polling every 60s.
export function NotificationBanner() {
  const online = useOnlineStatus();
  const studentId = useStudentStore((s) => s.studentId);
  const { data } = useNotifications(studentId);
  const [dismissedKey, setDismissedKey] = useState<string | null>(null);

  if (!online) return null; // offline banner takes priority, see OfflineBanner
  const banner = data?.banner;
  if (!banner) return null;

  const key = `${banner.type}:${banner.message}`;
  if (key === dismissedKey) return null;

  return (
    <div className={`notif-banner ${banner.type}`}>
      <p>{banner.message}</p>
      <button className="dismiss" onClick={() => setDismissedKey(key)}>
        Dismiss
      </button>
    </div>
  );
}
