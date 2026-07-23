"use client";

import type { TaskItem } from "@/lib/store";

interface TaskCardProps {
  task: TaskItem;
  onStart: (task: TaskItem) => void;
}

const BUTTON_LABEL: Record<TaskItem["status"], string> = {
  default: "Start",
  in_progress: "Continue",
  done: "Done ✓",
  overdue: "Start",
};

export function TaskCard({ task, onStart }: TaskCardProps) {
  const isDone = task.status === "done";
  const cardClass = task.status === "overdue" ? "task-card overdue" : "task-card";
  const btnClass = isDone ? "task-btn done" : "task-btn";

  return (
    <div className={cardClass}>
      <div className={`goal-badge ${task.goalType}`}>
        {task.goalType === "academic" ? "Academic" : "Career"}
      </div>
      <div>
        <p>{task.title}</p>
        <small>{task.reason}</small>
      </div>
      <button
        className={btnClass}
        disabled={isDone}
        onClick={() => !isDone && onStart(task)}
      >
        {BUTTON_LABEL[task.status]}
      </button>
    </div>
  );
}
