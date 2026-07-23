import os
from typing import Literal, Optional
from fastapi import APIRouter, BackgroundTasks, Query, HTTPException
from pydantic import BaseModel
from backend.connectors.github_connector import github_connector
from backend.logic.roadmap import db as roadmap_db, generate_roadmap
from backend.logic.streak import db as streak_db

router = APIRouter(prefix="/leetcode", tags=["leetcode"])

# Curated static problem list filtered by roadmap topic
CURATED_PROBLEMS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "link": "https://leetcode.com/problems/two-sum",
        "difficulty": "easy",
        "tags": ["array", "hash-table"],
        "topic": "leetcode-easy"
    },
    {
        "id": "valid-parentheses",
        "title": "Valid Parentheses",
        "link": "https://leetcode.com/problems/valid-parentheses",
        "difficulty": "easy",
        "tags": ["stack"],
        "topic": "leetcode-easy"
    },
    {
        "id": "merge-two-sorted-lists",
        "title": "Merge Two Sorted Lists",
        "link": "https://leetcode.com/problems/merge-two-sorted-lists",
        "difficulty": "easy",
        "tags": ["linked-list"],
        "topic": "leetcode-easy"
    },
    {
        "id": "longest-substring-without-repeating-characters",
        "title": "Longest Substring Without Repeating Characters",
        "link": "https://leetcode.com/problems/longest-substring-without-repeating-characters",
        "difficulty": "medium",
        "tags": ["hash-table", "string", "sliding-window"],
        "topic": "leetcode-medium"
    },
    {
        "id": "3sum",
        "title": "3Sum",
        "link": "https://leetcode.com/problems/3sum",
        "difficulty": "medium",
        "tags": ["array", "two-pointers", "sorting"],
        "topic": "leetcode-medium"
    },
    {
        "id": "container-with-most-water",
        "title": "Container With Most Water",
        "link": "https://leetcode.com/problems/container-with-most-water",
        "difficulty": "medium",
        "tags": ["array", "two-pointers", "greedy"],
        "topic": "leetcode-medium"
    },
    {
        "id": "git-basics",
        "title": "Git Basics & Workflow",
        "link": "https://github.com/features/actions",
        "difficulty": "easy",
        "tags": ["git", "github"],
        "topic": "git-github"
    }
]

class LeetcodeSubmission(BaseModel):
    student_id: str
    problem: str
    difficulty: str
    time_taken_seconds: int
    attempts: int
    solved_at: str

def on_push_confirm_task(student_id: str, problem_id: str):
    """
    Background task execution logic to poll/verify GitHub and update database.
    """
    try:
        latest_commit = github_connector.get_latest_commit(student_id)
        meta = github_connector.extract_file(latest_commit, "meta.json")
        if meta:
            if student_id not in roadmap_db._LEETCODE_SUBMISSIONS:
                roadmap_db._LEETCODE_SUBMISSIONS[student_id] = []
            
            sub_dict = {
                "problem": meta.get("problem", problem_id),
                "difficulty": meta.get("difficulty", "Easy"),
                "time_taken_seconds": meta.get("time_taken_seconds", 0),
                "attempts": meta.get("attempts", 1),
                "solved_at": meta.get("solved_at", ""),
            }
            roadmap_db._LEETCODE_SUBMISSIONS[student_id].append(sub_dict)
            
            # Write to SQLModel database table
            try:
                from backend.database import engine, LeetcodeSubmission as DBLeetcodeSubmission
                from sqlmodel import Session
                with Session(engine) as session:
                    db_sub = DBLeetcodeSubmission(
                        student_id=student_id,
                        problem=sub_dict["problem"],
                        difficulty=sub_dict["difficulty"],
                        time_taken_seconds=sub_dict["time_taken_seconds"],
                        attempts=sub_dict["attempts"],
                        solved_at=sub_dict["solved_at"]
                    )
                    session.add(db_sub)
                    session.commit()
            except Exception as dbe:
                print(f"Error persisting Leetcode submission to DB: {dbe}")
            
            # Record career activity for today
            streak_db._CAREER_ACTIVE_TODAY[student_id] = True
    except Exception as e:
        print(f"Error in background push-confirm: {e}")

@router.get("/problems")
def get_problems(
    student_id: Optional[str] = Query(None, description="The ID of the student to filter by roadmap topic"),
    topic: Optional[str] = Query(None, description="Explicit topic to filter by")
):
    """
    Serves the curated static problem list filtered by topic or the student's current roadmap topic.
    """
    target_topics = set()
    
    if topic:
        target_topics.add(topic.lower())
    elif student_id:
        try:
            roadmap = generate_roadmap(student_id)
            for day in roadmap:
                if day.topic:
                    target_topics.add(day.topic.lower())
        except Exception:
            pass

    if not target_topics:
        return CURATED_PROBLEMS

    filtered = [p for p in CURATED_PROBLEMS if p["topic"].lower() in target_topics]
    return filtered

@router.post("/{problem_id}/push-confirm")
def push_confirm(
    problem_id: str,
    student_id: str = Query(..., description="The ID of the student"),
    background_tasks: BackgroundTasks = None
):
    """
    Called when a student taps 'I've pushed my solution'.
    Triggers GitHub check. Run asynchronously in BackgroundTasks.
    """
    if background_tasks:
        background_tasks.add_task(on_push_confirm_task, student_id, problem_id)
        
    latest_commit = github_connector.get_latest_commit(student_id)
    meta = github_connector.extract_file(latest_commit, "meta.json")
    if meta:
        # Store in roadmap DB
        if student_id not in roadmap_db._LEETCODE_SUBMISSIONS:
            roadmap_db._LEETCODE_SUBMISSIONS[student_id] = []
            
        sub_dict = {
            "problem": meta.get("problem", problem_id),
            "difficulty": meta.get("difficulty", "Easy"),
            "time_taken_seconds": meta.get("time_taken_seconds", 0),
            "attempts": meta.get("attempts", 1),
            "solved_at": meta.get("solved_at", ""),
        }
        roadmap_db._LEETCODE_SUBMISSIONS[student_id].append(sub_dict)
        
        # Write to SQLModel database table
        try:
            from backend.database import engine, LeetcodeSubmission as DBLeetcodeSubmission
            from sqlmodel import Session
            with Session(engine) as session:
                db_sub = DBLeetcodeSubmission(
                    student_id=student_id,
                    problem=sub_dict["problem"],
                    difficulty=sub_dict["difficulty"],
                    time_taken_seconds=sub_dict["time_taken_seconds"],
                    attempts=sub_dict["attempts"],
                    solved_at=sub_dict["solved_at"]
                )
                session.add(db_sub)
                session.commit()
        except Exception as dbe:
            print(f"Error persisting Leetcode submission to DB: {dbe}")
        
        # Record career activity for today
        streak_db._CAREER_ACTIVE_TODAY[student_id] = True
        return { "status": "ok" }
        
    return { "status": "pending", "reason": "meta.json not found in latest commit yet" }

