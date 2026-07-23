"use client";

import { useState } from "react";
import { useStudentStore } from "@/lib/store-provider";
import { useRoadmap } from "@/lib/hooks";
import { api } from "@/lib/api";
import type { TaskItem } from "@/lib/store";
import type { RoadmapResponse } from "@/lib/types";
import { TaskCard } from "@/components/task-card/TaskCard";
import { TaskCardSkeleton } from "@/components/skeleton/TaskCardSkeleton";
import { StateBlock } from "@/components/state/StateBlock";
import { QuizCard } from "@/components/quiz-card/QuizCard";

function formatDayLabel(dateStr: string): string {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;
  const today = new Date();
  const diffDays = Math.round((date.setHours(0, 0, 0, 0) - today.setHours(0, 0, 0, 0)) / 86_400_000);
  const formatted = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  if (diffDays === 0) return `Today · ${formatted}`;
  if (diffDays === 1) return `Tomorrow · ${formatted}`;
  return formatted;
}

export default function RoadmapPage() {
  const studentId = useStudentStore((s) => s.studentId);
  const { data, error, isLoading, mutate } = useRoadmap(studentId);
  const [activeQuizTask, setActiveQuizTask] = useState<TaskItem | null>(null);

  function setTaskStatus(taskId: string, status: TaskItem["status"]) {
    mutate(
      (current: RoadmapResponse | undefined) =>
        current && {
          days: current.days.map((d) => ({
            ...d,
            items: d.items.map((i) => (i.id === taskId ? { ...i, status } : i)),
          })),
        },
      { revalidate: false }
    );
  }

  function onCompleteTask(task: TaskItem) {
    setTaskStatus(task.id, "done");
    api
      .post(`/tasks/${task.id}/complete`, { student_id: studentId })
      .catch(() => setTaskStatus(task.id, task.status))
      .finally(() => mutate());
  }

  const days = data?.days ?? [];

  return (
    <section className="tab-panel active" id="tab-roadmap">
      <div className="section-label">Prerequisite-aware roadmap</div>

      {isLoading && <TaskCardSkeleton count={4} />}

      {error && (
        <StateBlock
          variant="error"
          message="Couldn't load the roadmap."
          ctaLabel="Retry"
          onCta={() => mutate()}
        />
      )}

      {!isLoading && !error && days.length === 0 && (
        <StateBlock message="Complete your first module or push a commit to see tasks appear here." />
      )}

      {days.map((day) => (
        <div className="day-group" key={day.date}>
          <div className="day-head">
            <h3>{formatDayLabel(day.date)}</h3>
            <span>
              {day.items.length} item{day.items.length === 1 ? "" : "s"}
            </span>
          </div>
          {day.items.map((task) => (
            <TaskCard key={task.id} task={task} onStart={setActiveQuizTask} />
          ))}
        </div>
      ))}

      {activeQuizTask && (
        <div className="modal-overlay" onClick={() => setActiveQuizTask(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <QuizCard
              topic={activeQuizTask.title}
              goalType={activeQuizTask.goalType}
              onClose={() => setActiveQuizTask(null)}
              onComplete={() => onCompleteTask(activeQuizTask)}
            />
          </div>
        </div>
      )}
    </section>
  );
}
