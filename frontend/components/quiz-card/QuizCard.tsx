"use client";

import { useState } from "react";
import useSWR from "swr";
import { api, fetcher } from "@/lib/api";
import type { QuizResponse } from "@/lib/types";
import { StateBlock } from "@/components/state/StateBlock";

interface QuizCardProps {
  topic: string;
  goalType: "academic" | "career";
  onClose: () => void;
  onComplete?: () => void; // reuses the launching task's own completion path
}

export function QuizCard({ topic, goalType, onClose, onComplete }: QuizCardProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const { data, error, isLoading, mutate } = useSWR<QuizResponse>(
    ["/quiz/generate", topic, goalType],
    () => api.post<QuizResponse>("/quiz/generate", { topic, goal_type: goalType })
  );

  if (isLoading) {
    return (
      <div className="quiz-card">
        <div className="skel skel-line w-40" style={{ height: 14, marginBottom: 18 }} />
        <div className="skel skel-line w-60" style={{ height: 16, marginBottom: 16 }} />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="skel skel-line" style={{ height: 40, marginBottom: 8 }} />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="quiz-card">
        <StateBlock
          variant="error"
          message="Couldn't generate this quiz right now."
          ctaLabel="Retry"
          onCta={() => mutate()}
        />
        <div className="quiz-actions" style={{ marginTop: 12 }}>
          <button className="task-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    );
  }

  if (data.questions.length === 0) {
    return (
      <div className="quiz-card">
        <StateBlock message="No questions came back for this topic yet." />
        <div className="quiz-actions" style={{ marginTop: 12 }}>
          <button className="task-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    );
  }

  const allAnswered = data.questions.every((_, i) => answers[i] !== undefined);
  const correctCount = data.questions.filter((q, i) => answers[i] === q.answer).length;

  return (
    <div className="quiz-card">
      <div className="quiz-progress">{data.topic} · {data.questions.length} questions</div>
      {data.questions.map((question, qi) => (
        <div key={qi} style={{ marginBottom: 20 }}>
          <p className="quiz-question">
            {qi + 1}. {question.q}
          </p>
          <div className="quiz-options">
            {question.options.map((option) => {
              const isSelected = answers[qi] === option;
              const isCorrectOption = option === question.answer;
              let cls = "quiz-option";
              if (submitted) {
                if (isCorrectOption) cls += " correct";
                else if (isSelected) cls += " incorrect";
              } else if (isSelected) {
                cls += " selected";
              }
              return (
                <button
                  key={option}
                  className={cls}
                  disabled={submitted}
                  onClick={() => setAnswers((a) => ({ ...a, [qi]: option }))}
                >
                  {option}
                </button>
              );
            })}
          </div>
        </div>
      ))}

      {submitted ? (
        <>
          <p className="quiz-result">
            {correctCount} / {data.questions.length} correct
          </p>
          <div className="quiz-actions">
            <button
              className="quiz-btn"
              onClick={() => {
                onComplete?.();
                onClose();
              }}
            >
              Finish
            </button>
          </div>
        </>
      ) : (
        <div className="quiz-actions">
          <button className="task-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="quiz-btn"
            disabled={!allAnswered}
            onClick={() => setSubmitted(true)}
          >
            Submit
          </button>
        </div>
      )}
    </div>
  );
}
