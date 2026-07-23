// Wire types. Confirmed-live shapes are cross-checked against the backend's
// actual routes/schemas (backend/routes/*.py, backend/schemas/*.py) — not the
// task list's descriptions. Types under "not-yet-live" have no backend route
// yet; they exist so the UI/hooks can be built against a frozen shape ahead
// of the connector landing.

import type { TaskItem } from "./store";

export type Confidence = "low" | "medium" | "high";

// ---- GET /tasks/today (confirmed live) ----
export interface TodayResponse {
  tasks: TaskItem[];
  streak: { count: number; academicDone: boolean; careerActive: boolean };
  readiness: { academic: number; career: number; confidence: Confidence };
}

// ---- GET /roadmap?student_id= (confirmed live) ----
export interface RoadmapDay {
  date: string;
  items: TaskItem[];
}
export interface RoadmapResponse {
  days: RoadmapDay[];
}

// ---- GET /dashboard/{student_id} (confirmed live) ----
export interface DashboardResponse {
  academic: {
    readiness: number;
    confidence: Confidence;
    subjects: Record<string, number[]>;
  };
  career: {
    readiness: number;
    confidence: Confidence;
    activity_trend: number[];
    streak: number;
  };
}

// ---- POST /chat/message (confirmed live) ----
export interface ChatMessageResponse {
  reply: string;
}

// ---- POST /intake/turn (confirmed live) ----
export interface IntakeTurnResponse {
  next_question: string | null;
  quick_replies: string[];
  done: boolean;
}

// ---- POST /quiz/generate (confirmed live) ----
export interface QuizQuestion {
  q: string;
  options: string[];
  answer: string;
}
export interface QuizResponse {
  topic: string;
  questions: QuizQuestion[];
}

// ---- GET /struggle/offers, POST /struggle/offers/{id}/respond (confirmed live) ----
export interface StruggleOffer {
  offer_id: string;
  topic: string;
  goal_type: "academic" | "career";
  reason: string;
}
export interface StruggleOffersResponse {
  offers: StruggleOffer[];
}

// ---- GET /notifications?student_id= (confirmed live) ----
export interface NotificationBannerData {
  type: "streak-at-risk" | "resume-bullet-ready" | "reminder" | "offline";
  message: string;
  priority: number;
}
export interface NotificationsResponse {
  banner: NotificationBannerData | null;
}

// ---- POST /resume/bullets/{id}/feedback (confirmed live) ----
export type ResumeFeedbackOutcome = "yes" | "no" | "somewhat";
export interface ResumeBulletFeedback {
  bullet_id: string;
  outcome: ResumeFeedbackOutcome;
}

// ---- Resume bullet itself (NOT confirmed live — generate_resume_bullet()
// exists in backend/logic/resume.py but is not mounted behind any route in
// backend/routes/. No GET /resume/bullets exists. Kept here so the card can
// be built against the documented shape and flagged as not-connected.) ----
export interface ResumeBullet {
  id: string;
  text: string;
  evidence_link: string;
}

// ---- Captured intake profile (NOT confirmed live — backend/logic/intake.py
// stores target role / weekly hours only as free-text inside its internal
// IntakeState.answers list, and nothing in backend/routes/ exposes a GET
// that returns them back out in structured form. Kept here so the Goals
// page's summary card can be built against the documented shape and
// flagged as not-connected, same as the LMS/LeetCode/Jobs placeholders
// below.) ----
export interface IntakeProfile {
  targetRole: string;
  weeklyHours: number;
}

// ---- NOT YET LIVE: no backend route exists for any of the below. Shapes
// are the documented placeholders from the Frontend/Integration Spec, used
// only to type the SWR hooks and render honest "not connected" states. ----

// Server-owned fields only — "pushed" status is derived client-side (the
// timer store + a local push-confirmed set), not part of the response.
export interface LeetCodeProblem {
  id: string;
  title: string;
  link: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string[];
}

export interface JobListing {
  id: string;
  title: string;
  company: string;
  matchPct: number;
  missingSkills: string[];
}

// LMS Integration Spec — six connector methods, frozen response shapes.
export interface LmsStudentProfile {
  name: string;
  program: string;
  year: number;
  rollNumber: string;
}
export interface LmsSubject {
  name: string;
  code: string;
  instructor: string;
}
export interface LmsQuizScore {
  subject: string;
  quiz: string;
  score: number;
  maxScore: number;
  date: string;
}
export interface LmsAssignment {
  subject: string;
  title: string;
  dueDate: string;
  submitted: boolean;
}
export interface LmsProgrammingProgress {
  language: string;
  modulesCompleted: number;
  modulesTotal: number;
}
export interface LmsExamScheduleItem {
  subject: string;
  date: string;
  time: string;
}
