"""Daily Micro-Test Generator (Backend Spec §8, PRD §4.9).

3-5 questions per completed topic, academic or career. Reuses Phase 1's
call_and_validate — same pattern as intake (§7).

Fallback (§4.3): on LLMValidationFailed, skip today's quiz for that
topic and keep prior roadmap state — never crash. The fallback is
represented as a MicroTestResponse with an empty `questions` list
(the topic itself is preserved) so callers can keep the documented
return type `MicroTestResponse` rather than handling `None`/exceptions;
callers should treat an empty `questions` list as "no quiz today."
"""

from typing import Literal

from backend.llm.validation import LLMValidationFailed, call_and_validate
from backend.schemas.quiz import MicroTestResponse

QUIZ_SYSTEM_PROMPT = """You are ZenoAI's daily micro-test generator.

Generate 3-5 multiple-choice questions on the given topic. Tailor question
style and difficulty to the goal type provided in the prompt: "academic"
questions test conceptual/exam-style understanding, "career" questions test
practical/interview-style application.

Each question must have a "q" (question text), "options" (a list of answer
choices), and "answer" (the correct option, must be one of the strings in
"options").

Respond with ONLY raw JSON, no markdown fences, no prose, matching exactly:
{"topic": "<string>", "questions": [{"q": "<string>", "options": ["<string>", ...], "answer": "<string>"}, ...]}
"""


def generate_quiz(topic: str, goal_type: Literal["academic", "career"]) -> MicroTestResponse:
    try:
        return call_and_validate(
            QUIZ_SYSTEM_PROMPT,
            f"Generate 3-5 questions on: {topic} (goal_type: {goal_type})",
            MicroTestResponse,
        )
    except LLMValidationFailed:
        # Skip today's quiz for this topic, keep prior roadmap state — never crash.
        return MicroTestResponse(topic=topic, questions=[])
