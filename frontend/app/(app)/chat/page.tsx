"use client";

import { useEffect, useRef, useState } from "react";
import { useStudentStore } from "@/lib/store-provider";
import { useStruggleOffers } from "@/lib/hooks";
import { api } from "@/lib/api";
import type { ChatMessageResponse } from "@/lib/types";
import { StruggleOfferBanner } from "@/components/struggle-offer-banner/StruggleOfferBanner";

const FALLBACK_TEXT = "Mentor AI needs a breather — try again in a moment.";

export default function ChatPage() {
  const studentId = useStudentStore((s) => s.studentId);
  const chat = useStudentStore((s) => s.chat);
  const sendChatMessage = useStudentStore((s) => s.sendChatMessage);
  const receiveChatReply = useStudentStore((s) => s.receiveChatReply);
  const failChatReply = useStudentStore((s) => s.failChatReply);
  const retryLastChatMessage = useStudentStore((s) => s.retryLastChatMessage);

  const { data: offersData, mutate: mutateOffers } = useStruggleOffers(studentId);

  const [input, setInput] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  // Same rationale as Today's page (PRD §11 Stage A is data-collection
  // only, never suppresses the underlying signal) — dismissal has to be
  // tracked client-side, current-session only.
  const [dismissedOfferIds, setDismissedOfferIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [chat.messages.length, chat.pending]);

  function askMentor(message: string) {
    api
      .post<ChatMessageResponse>("/chat/message", { student_id: studentId, message })
      .then((res) => receiveChatReply(res.reply))
      .catch(() => failChatReply(FALLBACK_TEXT));
  }

  function onSend() {
    const text = input.trim();
    if (!text || chat.pending) return;
    setInput("");
    sendChatMessage(text);
    askMentor(text);
  }

  function onRetry() {
    retryLastChatMessage();
    askMentor(chat.lastUserText);
  }

  function onRespondOffer(offerId: string, accepted: boolean) {
    setDismissedOfferIds((prev) => new Set(prev).add(offerId));
    api
      .post(`/struggle/offers/${offerId}/respond`, { accepted, features: {} })
      .catch(() => {
        setDismissedOfferIds((prev) => {
          const next = new Set(prev);
          next.delete(offerId);
          return next;
        });
      });
  }

  const visibleOffers = (offersData?.offers ?? []).filter((o) => !dismissedOfferIds.has(o.offer_id));

  return (
    <section className="tab-panel active" id="tab-chat">
      <div className="section-label">Mentor AI Chat — same store as Today</div>

      <StruggleOfferBanner offers={visibleOffers} onRespond={onRespondOffer} />

      <div className="chat-shell">
        <div className="chat-log" ref={logRef}>
          {chat.messages.length === 0 && !chat.pending && (
            <div className="bubble bot">
              Ask me anything about your roadmap, a topic you&apos;re stuck on, or what to do next.
            </div>
          )}
          {chat.messages.map((m) => (
            <div key={m.id} className={`bubble ${m.role}${m.failed ? " failed" : ""}`}>
              {m.text}
              {m.failed && (
                <button className="bubble-retry" onClick={onRetry}>
                  Retry
                </button>
              )}
            </div>
          ))}
          {chat.pending && (
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}
        </div>
        <div className="chat-input">
          <input
            type="text"
            placeholder="Type a reply…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSend()}
          />
          <button onClick={onSend} disabled={chat.pending || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </section>
  );
}