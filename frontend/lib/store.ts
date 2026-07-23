import { createStore } from "zustand";

export type TaskStatus = "default" | "in_progress" | "done" | "overdue";

export interface TaskItem {
  id: string;
  goalType: "academic" | "career";
  title: string;
  reason: string; // e.g. "exam in 18 days"
  status: TaskStatus;
}

export interface Readiness {
  academic: number;
  career: number;
  confidence: "low" | "medium" | "high";
}

export interface StreakState {
  count: number;
  academicDone: boolean;
  careerActive: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
  failed?: boolean; // bot fallback reply — shows a retry affordance on this bubble only
}

export interface ChatState {
  messages: ChatMessage[];
  pending: boolean; // typing-dots while POST /chat/message is in flight
  lastUserText: string; // needed so the retry affordance can resend the same turn
}

export interface LeetCodeTimerState {
  problemId: string;
  startedAt: number; // epoch ms — survives navigation since it lives in the store, not component state
}

export interface StudentStore {
  studentId: string;
  tasks: TaskItem[]; // today's merged academic+career tasks
  streak: StreakState;
  readiness: Readiness;
  chat: ChatState;
  leetcodeTimer: LeetCodeTimerState | null;

  setStudentId: (id: string) => void;
  setTasks: (tasks: TaskItem[]) => void;
  setStreak: (streak: StreakState) => void;
  completeTask: (taskId: string) => void; // optimistic, UI/UX Spec §5.1
  revertTask: (taskId: string) => void; // rollback on API failure
  incrementStreak: () => void;
  setReadiness: (r: Readiness) => void;

  sendChatMessage: (text: string) => void; // appends user bubble, marks pending
  receiveChatReply: (text: string) => void; // appends bot bubble, clears pending
  failChatReply: (fallbackText: string) => void; // appends failed bot bubble, clears pending
  retryLastChatMessage: () => void; // clears the failed flag on the last bubble, re-marks pending

  startLeetcodeTimer: (problemId: string) => void;
  stopLeetcodeTimer: () => void;
}

export type StudentStoreApi = ReturnType<typeof createStudentStore>;

let _msgId = 0;
const nextMsgId = () => `msg-${++_msgId}-${Date.now()}`;

// Factory — never call this at module scope. See lib/store-provider.tsx.
export function createStudentStore(initial?: Partial<StudentStore>) {
  return createStore<StudentStore>((set) => ({
    studentId: "",
    tasks: [],
    streak: { count: 0, academicDone: false, careerActive: false },
    readiness: { academic: 0, career: 0, confidence: "low" },
    chat: { messages: [], pending: false, lastUserText: "" },
    leetcodeTimer: null,

    setStudentId: (id) => set({ studentId: id }),
    setTasks: (tasks) => set({ tasks }),
    setStreak: (streak) => set({ streak }),
    completeTask: (taskId) =>
      set((s) => ({
        tasks: s.tasks.map((t) =>
          t.id === taskId ? { ...t, status: "done" } : t
        ),
      })),
    revertTask: (taskId) =>
      set((s) => ({
        tasks: s.tasks.map((t) =>
          t.id === taskId ? { ...t, status: "default" } : t
        ),
      })),
    incrementStreak: () =>
      set((s) => ({ streak: { ...s.streak, count: s.streak.count + 1 } })),
    setReadiness: (r) => set({ readiness: r }),

    sendChatMessage: (text) =>
      set((s) => ({
        chat: {
          messages: [...s.chat.messages, { id: nextMsgId(), role: "user", text }],
          pending: true,
          lastUserText: text,
        },
      })),
    receiveChatReply: (text) =>
      set((s) => ({
        chat: {
          ...s.chat,
          messages: [...s.chat.messages, { id: nextMsgId(), role: "bot", text }],
          pending: false,
        },
      })),
    failChatReply: (fallbackText) =>
      set((s) => ({
        chat: {
          ...s.chat,
          messages: [
            ...s.chat.messages,
            { id: nextMsgId(), role: "bot", text: fallbackText, failed: true },
          ],
          pending: false,
        },
      })),
    retryLastChatMessage: () =>
      set((s) => ({ chat: { ...s.chat, pending: true } })),

    startLeetcodeTimer: (problemId) =>
      set({ leetcodeTimer: { problemId, startedAt: Date.now() } }),
    stopLeetcodeTimer: () => set({ leetcodeTimer: null }),

    ...initial,
  }));
}
