// Typed SWR hooks, one per backend endpoint. Confirmed-live endpoints hit
// lib/api.ts's fetcher for real. Not-yet-live endpoints (no route exists in
// backend/routes/) are typed identically but the calling component must
// render a "not connected" state instead of trusting the data — see each
// component under components/leetcode, components/job-card, components/lms.

import useSWR from "swr";
import { fetcher as rawFetcher } from "./api";
import type {
  DashboardResponse,
  GithubStatus,
  IntakeProfile,
  JobListing,
  LeetCodeProblem,
  LmsAssignment,
  LmsExamScheduleItem,
  LmsProgrammingProgress,
  LmsQuizScore,
  LmsStudentProfile,
  LmsSubject,
  NotificationsResponse,
  ResumeBullet,
  RoadmapResponse,
  StruggleOffersResponse,
  TodayResponse,
} from "./types";


function typedFetcher<T>(path: string): Promise<T> {
  return rawFetcher(path) as Promise<T>;
}

// ---- confirmed-live ----

export function useToday(studentId: string) {
  return useSWR<TodayResponse>(
    studentId ? `/tasks/today?student_id=${studentId}` : null,
    typedFetcher<TodayResponse>
  );
}

export function useRoadmap(studentId: string) {
  return useSWR<RoadmapResponse>(
    studentId ? `/roadmap?student_id=${studentId}` : null,
    typedFetcher<RoadmapResponse>
  );
}

export function useDashboard(studentId: string) {
  return useSWR<DashboardResponse>(
    studentId ? `/dashboard/${studentId}` : null,
    typedFetcher<DashboardResponse>
  );
}

export function useStruggleOffers(studentId: string) {
  return useSWR<StruggleOffersResponse>(
    studentId ? `/struggle/offers?student_id=${studentId}` : null,
    typedFetcher<StruggleOffersResponse>
  );
}

export function useNotifications(studentId: string) {
  return useSWR<NotificationsResponse>(
    studentId ? `/notifications?student_id=${studentId}` : null,
    typedFetcher<NotificationsResponse>,
    { refreshInterval: 60_000 }
  );
}

export function useGithubStatus(studentId: string) {
  return useSWR<GithubStatus>(
    studentId ? `/auth/github/status?student_id=${studentId}` : null,
    typedFetcher<GithubStatus>
  );
}

// ---- documented but not yet live on the backend — hooks are real and
// typed, but every route below 404s against the current backend. Each
// caller must show a "not connected" state, never fall back to fixture
// data. ----

export function useIntakeProfile(studentId: string) {
  return useSWR<IntakeProfile>(
    studentId ? `/intake/profile?student_id=${studentId}` : null,
    typedFetcher<IntakeProfile>
  );
}

export function useResumeBullets(studentId: string) {
  return useSWR<ResumeBullet[]>(
    studentId ? `/resume/bullets?student_id=${studentId}` : null,
    typedFetcher<ResumeBullet[]>
  );
}

export function useLeetCodeProblems(studentId: string) {
  return useSWR<LeetCodeProblem[]>(
    studentId ? `/leetcode/problems?student_id=${studentId}` : null,
    typedFetcher<LeetCodeProblem[]>
  );
}

export function useJobs(studentId: string) {
  return useSWR<JobListing[]>(
    studentId ? `/jobs?student_id=${studentId}` : null,
    typedFetcher<JobListing[]>
  );
}

export function useLmsStudentProfile(studentId: string) {
  return useSWR<LmsStudentProfile>(
    studentId ? `/lms/profile?student_id=${studentId}` : null,
    typedFetcher<LmsStudentProfile>
  );
}

export function useLmsSubjects(studentId: string) {
  return useSWR<LmsSubject[]>(
    studentId ? `/lms/subjects?student_id=${studentId}` : null,
    typedFetcher<LmsSubject[]>
  );
}

export function useLmsQuizScores(studentId: string) {
  return useSWR<LmsQuizScore[]>(
    studentId ? `/lms/quiz-scores?student_id=${studentId}` : null,
    typedFetcher<LmsQuizScore[]>
  );
}

export function useLmsAssignments(studentId: string) {
  return useSWR<LmsAssignment[]>(
    studentId ? `/lms/assignments?student_id=${studentId}` : null,
    typedFetcher<LmsAssignment[]>
  );
}

export function useLmsProgrammingProgress(studentId: string) {
  return useSWR<LmsProgrammingProgress[]>(
    studentId ? `/lms/programming-progress?student_id=${studentId}` : null,
    typedFetcher<LmsProgrammingProgress[]>
  );
}

export function useLmsExamSchedule(studentId: string) {
  return useSWR<LmsExamScheduleItem[]>(
    studentId ? `/lms/exam-schedule?student_id=${studentId}` : null,
    typedFetcher<LmsExamScheduleItem[]>
  );
}
