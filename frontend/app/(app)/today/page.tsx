"use client";

import { useEffect, useState } from "react";
import { useStudentStore } from "@/lib/store-provider";
import { useToday, useRoadmap, useStruggleOffers } from "@/lib/hooks";
import { api } from "@/lib/api";
import type { TaskItem } from "@/lib/store";
import { TaskCard } from "@/components/task-card/TaskCard";
import { TaskCardSkeleton } from "@/components/skeleton/TaskCardSkeleton";
import { StateBlock } from "@/components/state/StateBlock";
import { StruggleOfferBanner } from "@/components/struggle-offer-banner/StruggleOfferBanner";
import { QuizCard } from "@/components/quiz-card/QuizCard";

export default function TodayPage() {
  const studentId = useStudentStore((s) => s.studentId);
  const tasks = useStudentStore((s) => s.tasks);
  const streak = useStudentStore((s) => s.streak);
  const readiness = useStudentStore((s) => s.readiness);
  const setTasks = useStudentStore((s) => s.setTasks);
  const setStreak = useStudentStore((s) => s.setStreak);
  const setReadiness = useStudentStore((s) => s.setReadiness);
  const completeTask = useStudentStore((s) => s.completeTask);
  const revertTask = useStudentStore((s) => s.revertTask);
  const incrementStreak = useStudentStore((s) => s.incrementStreak);

  const { data, error, isLoading, mutate } = useToday(studentId);
  const { data: roadmapData } = useRoadmap(studentId);
  const { data: offersData, mutate: mutateOffers } = useStruggleOffers(studentId);

  const [activeQuizTask, setActiveQuizTask] = useState<TaskItem | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // Chat never issues its own /tasks fetch (Frontend Spec §5.4) — Today
  // owns the fetch, both screens read from the shared store.
  useEffect(() => {
    if (!data) return;
    setTasks(data.tasks);
    setStreak(data.streak);
    setReadiness(data.readiness);
  }, [data, setTasks, setStreak, setReadiness]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(t);
  }, [toast]);

  function onTaskComplete(task: TaskItem) {
    const dualGateAlreadyMet = streak.academicDone && streak.careerActive;
    completeTask(task.id);
    if (task.goalType === "academic") {
      setStreak({ ...streak, academicDone: true });
      if (!dualGateAlreadyMet && streak.careerActive) incrementStreak();
    }

    api.post(`/tasks/${task.id}/complete`, { student_id: studentId }).catch(() => {
      revertTask(task.id);
      setToast("Couldn't save that — try again.");
    });
  }

  function onStartTask(task: TaskItem) {
    setActiveQuizTask(task);
  }

  function onRespondOffer(offerId: string, accepted: boolean) {
    api
      .post(`/struggle/offers/${offerId}/respond`, { accepted, features: {} })
      .finally(() => mutateOffers());
  }

  const days = roadmapData?.days ?? [];
  const weekItems = days.flatMap((d) => d.items.map((i) => ({ ...i, date: d.date })));
  const weekTotal = weekItems.length;
  const weekDone = weekItems.filter((i) => i.status === "done").length;
  const weekPending = weekItems.filter((i) => i.status !== "done");
  const acDonePct = weekTotal
    ? (weekItems.filter((i) => i.goalType === "academic" && i.status === "done").length / weekTotal) * 100
    : 0;
  const crDonePct = weekTotal
    ? (weekItems.filter((i) => i.goalType === "career" && i.status === "done").length / weekTotal) * 100
    : 0;

  return (
    <section className="tab-panel active" id="tab-today">
      <StruggleOfferBanner offers={offersData?.offers ?? []} onRespond={onRespondOffer} />

      <div className="section-label">Merged task list — today only</div>

      {isLoading && tasks.length === 0 && <TaskCardSkeleton count={3} />}

      {error && tasks.length === 0 && (
        <StateBlock
          variant="error"
          message="Couldn't load today's tasks."
          ctaLabel="Retry"
          onCta={() => mutate()}
        />
      )}

      {!isLoading && !error && tasks.length === 0 && (
        <StateBlock message="Complete your first module or push a commit to see tasks appear here." />
      )}

      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} onStart={onStartTask} />
      ))}

      <div className="readiness-strip">
        <div className="metric">
          <span className="rdot academic"></span>Academic Readiness{" "}
          <b>{Math.round(readiness.academic * 100)}%</b>
        </div>
        <div className="metric">
          <span className="rdot career"></span>Career Readiness{" "}
          <b>{Math.round(readiness.career * 100)}%</b>
        </div>
        <div className="readiness-note">
          Scored separately from verified evidence, never blended into one
          number.
        </div>
      </div>

      <div className="week-card">
        <div className="week-head">
          <h3>
            This week — {weekDone} of {weekTotal} tasks done
          </h3>
          <span>{weekPending.length} pending</span>
        </div>
        <div className="week-bar">
          <div className="seg ac" style={{ width: `${acDonePct}%` }}></div>
          <div className="seg cr" style={{ width: `${crDonePct}%` }}></div>
        </div>
        {weekPending.length === 0 ? (
          <div className="week-pending">
            <span className="wtitle">Nothing pending this week.</span>
          </div>
        ) : (
          weekPending.slice(0, 3).map((item) => (
            <div className="week-pending" key={item.id}>
              <span className={`wdot ${item.goalType === "academic" ? "ac" : "cr"}`}></span>
              <span className="wtitle">{item.title}</span>
              <span className="wdue">{item.date}</span>
            </div>
          ))
        )}
      </div>

      {activeQuizTask && (
        <div className="modal-overlay" onClick={() => setActiveQuizTask(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <QuizCard
              topic={activeQuizTask.title}
              goalType={activeQuizTask.goalType}
              onClose={() => setActiveQuizTask(null)}
              onComplete={() => onTaskComplete(activeQuizTask)}
            />
          </div>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </section>
  );
}
