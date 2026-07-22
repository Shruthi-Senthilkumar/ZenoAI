import os
import sys
import json
import psycopg2
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def generate_history():
    data = {}
    today = datetime.utcnow()
    
    # ------------------ STUDENT A: Strong Academic, Weak Career ------------------
    student_a_quiz_history = []
    # Rising scores
    subjects = ["DSA", "Python", "AI"]
    for i in range(15):
        day_date = today - timedelta(days=15-i)
        score_pct = 70 + (i * 1.8) # 70 to 97
        for sub in subjects:
            student_a_quiz_history.append({
                "subject": sub,
                "grade_pct": round(score_pct, 1),
                "subject_median": 75.0,
                "missed_topics": ["tree-traversal"] if score_pct < 80 else []
            })
            
    # GitHub: last commit was 6 days ago
    student_a_github = [
        {"repo": "zeno-app", "commits_today": 1, "last_commit": (today - timedelta(days=6)).isoformat() + "Z"}
    ]
    student_a_leetcode = [] # Low/no leetcode

    data["student_a"] = {
        "profile": {
            "name": "Abhay",
            "level": "Advanced",
            "skills": ["Python", "DSA", "SQL"],
            "goal": "Get SDE Job"
        },
        "quiz_scores": {"DSA": 95, "Python": 97, "AI": 92},
        "assignments": [
            {"assignment_name": "SQL Joins", "status": "completed", "due_date": "2026-07-20"},
            {"assignment_name": "OOP Polymorphism", "status": "completed", "due_date": "2026-07-22"}
        ],
        "programming_progress": [
            {"topic": "recursion", "status": "completed", "completion_pct": 100},
            {"topic": "trees", "status": "completed", "completion_pct": 100}
        ],
        "exam_schedule": [
            {"exam_name": "DBMS Endsem", "date": "2026-08-10", "duration_minutes": 180}
        ],
        "subject_trends": {
            "DSA": [70, 75, 82, 88, 95],
            "Python": [72, 78, 85, 92, 97],
            "AI": [68, 74, 80, 85, 92]
        },
        "career_activity_trend": [0.1, 0.1, 0.0, 0.0, 0.0],
        "recent_quiz_scores": student_a_quiz_history[-6:],
        "github_activity": student_a_github,
        "leetcode_submissions": student_a_leetcode,
        "evidence_levels": {
            "academic": {"limits": "shipped", "derivatives": "shipped", "integrals": "applied", "arrays": "shipped"},
            "career": {"git-github": "none", "leetcode-easy": "practiced"}
        },
        "skill_weights": {
            "academic": {"limits": 1.0, "derivatives": 2.0, "integrals": 2.0, "arrays": 1.0},
            "career": {"git-github": 1.0, "leetcode-easy": 3.0}
        },
        "days_since_last_commit": 6,
        "learning_profile": {
            "dbms": {"avg_score": 92, "trend": "up", "last_test": 95},
            "oop": {"avg_score": 94, "trend": "up", "last_test": 97},
            "derivatives": {"avg_score": 90, "trend": "up", "last_test": 92},
            
        },
        "intake_answers": {"oop": "confident", "python-basics": "confident"}
    }

    # ------------------ STUDENT B: Weak Academic, Strong Career ------------------
    student_b_quiz_history = []
    # Dipping Physics score
    for i in range(15):
        day_date = today - timedelta(days=15-i)
        physics_score = 88 - (i * 2.5) # 88 down to 50
        student_b_quiz_history.append({
            "subject": "Physics",
            "grade_pct": round(physics_score, 1),
            "subject_median": 75.0,
            "missed_topics": ["thermodynamics", "optics"] if physics_score < 70 else []
        })
        
    # GitHub: daily commits
    student_b_github = []
    for i in range(15):
        day_date = today - timedelta(days=15-i)
        student_b_github.append({
            "repo": "leetcode-solutions",
            "commits_today": 2 if i % 2 == 0 else 3,
            "last_commit": day_date.isoformat() + "Z"
        })
        
    # LeetCode: daily streak
    student_b_leetcode = []
    for i in range(10):
        day_date = today - timedelta(days=10-i)
        student_b_leetcode.append({
            "problem": f"Problem {i+1}",
            "difficulty": "Easy" if i < 5 else "Medium",
            "time_taken_seconds": 400 + i * 20,
            "attempts": 1 if i % 3 != 0 else 2,
            "solved_at": day_date.isoformat() + "Z"
        })

    data["student_b"] = {
        "profile": {
            "name": "Bala",
            "level": "Intermediate",
            "skills": ["Python"],
            "goal": "Improve coding"
        },
        "quiz_scores": {"Physics": 50, "DBMS": 82},
        "assignments": [
            {"assignment_name": "Physics Lab 3", "status": "pending", "due_date": "2026-07-24"},
            {"assignment_name": "DBMS Query Optimization", "status": "completed", "due_date": "2026-07-21"}
        ],
         
        "programming_progress": [
            {"topic": "arrays", "status": "completed", "completion_pct": 100},
            {"topic": "pointers", "status": "in_progress", "completion_pct": 60}
        ],
        "exam_schedule": [
            {"exam_name": "Physics Midsem", "date": "2026-08-05", "duration_minutes": 120}
        ],
        "subject_trends": {
            "Physics": [88, 80, 75, 68, 60, 50],
            "DBMS": [78, 80, 81, 82, 82]
        },
        "career_activity_trend": [0.6, 0.7, 0.75, 0.8, 0.9],
        "recent_quiz_scores": student_b_quiz_history[-6:],
        "github_activity": student_b_github,
        "leetcode_submissions": student_b_leetcode,
        "evidence_levels": {
            "academic": {"limits": "practiced", "derivatives": "practiced", "integrals": "none", "arrays": "applied"},
            "career": {"git-github": "shipped", "leetcode-easy": "shipped", "leetcode-medium": "applied"}
        },
        "skill_weights": {
            "academic": {"limits": 1.0, "derivatives": 2.0, "integrals": 2.0, "arrays": 1.0},
            "career": {"git-github": 1.0, "leetcode-easy": 3.0, "leetcode-medium": 2.0}
        },
        "days_since_last_commit": 0,
        "learning_profile": {
            "physics": {"avg_score": 50, "trend": "down", "last_test": 52},
            "dbms": {"avg_score": 82, "trend": "up", "last_test": 82},
            
        },
        "intake_answers": {"physics": "struggling", "python-basics": "confident"}
    }

    # ------------------ STUDENT C: Balanced, Moderate ------------------
    student_c_quiz_history = []
    # Steady moderate scores
    for i in range(15):
        score_pct = 72 + (i % 3)
        student_c_quiz_history.append({
            "subject": "DSA",
            "grade_pct": round(score_pct, 1),
            "subject_median": 75.0,
            "missed_topics": []
        })
        
    student_c_github = []
    for i in range(15):
        if i % 2 == 0:
            day_date = today - timedelta(days=15-i)
            student_c_github.append({
                "repo": "dev-project",
                "commits_today": 1,
                "last_commit": day_date.isoformat() + "Z"
            })
            
    student_c_leetcode = [
        {
            "problem": "Valid Palindrome",
            "difficulty": "Easy",
            "time_taken_seconds": 500,
            "attempts": 1,
            "solved_at": (today - timedelta(days=4)).isoformat() + "Z"
        }
    ]

    data["student_c"] = {
        "profile": {
            "name": "Chitra",
            "level": "Beginner",
            "skills": ["Basics"],
            "goal": "Learn programming"
        },
        "quiz_scores": {"DSA": 75, "Python": 73, "AI": 74},
        "assignments": [
            {"assignment_name": "Basic Syntax", "status": "completed", "due_date": "2026-07-15"}
        ],
        
        "programming_progress": [
            {"topic": "variables", "status": "completed", "completion_pct": 100}
        ],
        "exam_schedule": [],
        "subject_trends": {
            "DSA": [72, 73, 74, 75, 75],
            "Python": [71, 72, 73, 73, 74]
        },
        "career_activity_trend": [0.4, 0.45, 0.48, 0.5, 0.52],
        "recent_quiz_scores": student_c_quiz_history[-6:],
        "github_activity": student_c_github,
        "leetcode_submissions": student_c_leetcode,
        "evidence_levels": {
            "academic": {"limits": "practiced", "derivatives": "practiced", "integrals": "practiced"},
            "career": {"git-github": "applied", "leetcode-easy": "applied"}
        },
        "skill_weights": {
            "academic": {"limits": 1.0, "derivatives": 1.0, "integrals": 1.0},
            "career": {"git-github": 1.0, "leetcode-easy": 1.0}
        },
        "days_since_last_commit": 2,
        "learning_profile": {
            "dsa": {"avg_score": 75, "trend": "stable", "last_test": 75},
            "python": {"avg_score": 73, "trend": "stable", "last_test": 74},
        },
        "intake_answers": {"dsa": "moderate", "python-basics": "moderate"}
    }
    
    return data

def write_fixtures(data):
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    
    for s_key, s_data in data.items():
        s_dir = FIXTURES_DIR / s_key
        s_dir.mkdir(exist_ok=True)
        
        # Write individual files
        files_to_write = {
            "student_profile.json": s_data["profile"],
            "quiz_scores.json": s_data["quiz_scores"],
            "assignments.json": s_data["assignments"],
            "programming_progress.json": s_data["programming_progress"],
            "exam_schedule.json": s_data["exam_schedule"],
            "subject_trends.json": s_data["subject_trends"],
            "career_activity_trend.json": s_data["career_activity_trend"],
            "recent_quiz_scores.json": s_data["recent_quiz_scores"],
            "github_activity.json": s_data["github_activity"],
            "leetcode_submissions.json": s_data["leetcode_submissions"],
            "evidence_levels.json": s_data["evidence_levels"],
            "skill_weights.json": s_data["skill_weights"],
            "learning_profile.json": s_data["learning_profile"],
            "intake_answers.json": s_data["intake_answers"]
        }
        
        for name, content in files_to_write.items():
            f_path = s_dir / name
            f_path.write_text(json.dumps(content, indent=4))
            
    print("Successfully wrote JSON fixtures for student_a, student_b, and student_c.")

def seed_db(data):
    # 1. Seed SQLite database via SQLModel idempotently
    try:
        from backend.database import (
            init_db, engine, Student, LearningProfile, QuizScore,
            AssignmentEvent, GithubActivity, LeetcodeSubmission,
            ConnectorCapability, JobCache, ResumeBullet
        )
        from sqlmodel import Session, select, delete

        init_db()

        with Session(engine) as session:
            for s_key in ["student_a", "student_b", "student_c"]:
                s_data = data[s_key]

                # Delete existing rows for idempotency
                session.exec(delete(Student).where(Student.id == s_key))
                session.exec(delete(LearningProfile).where(LearningProfile.student_id == s_key))
                session.exec(delete(QuizScore).where(QuizScore.student_id == s_key))
                session.exec(delete(AssignmentEvent).where(AssignmentEvent.student_id == s_key))
                session.exec(delete(GithubActivity).where(GithubActivity.student_id == s_key))
                session.exec(delete(LeetcodeSubmission).where(LeetcodeSubmission.student_id == s_key))
                session.exec(delete(ConnectorCapability).where(ConnectorCapability.student_id == s_key))
                session.exec(delete(ResumeBullet).where(ResumeBullet.student_id == s_key))

                # Student profile
                student = Student(
                    id=s_key,
                    name=s_data["profile"]["name"],
                    target_role=s_data["profile"].get("goal", "Software Engineer"),
                    weekly_hours=15 if s_key == "student_a" else 20,
                    github_username=f"{s_key}_dev"
                )
                session.add(student)

                # Learning profile
                for subj, score in s_data["quiz_scores"].items():
                    trend = "up" if s_key == "student_a" else ("down" if subj == "Physics" else "flat")
                    
                    lp = LearningProfile(
                        student_id=s_key,
                        subject=subj,
                        avg_score=float(score),
                        trend=trend,
                        last_test=float(score),
                    )
                    session.add(lp)

                # Quiz scores
                for idx, q_item in enumerate(s_data.get("recent_quiz_scores", [])):
                    qs = QuizScore(
                        student_id=s_key,
                        course=q_item.get("subject", "General"),
                        quiz=f"{q_item.get('subject')} Quiz {idx+1}",
                        attempt=1,
                        marks=float(q_item.get("grade_pct", 80)),
                        grade_pct=float(q_item.get("grade_pct", 80)),
                        duration_seconds=900,
                        missed_topics=json.dumps(q_item.get("missed_topics", []))
                    )
                    session.add(qs)

                # Assignments
                for assign in s_data["assignments"]:
                    ae = AssignmentEvent(
                        student_id=s_key,
                        title=assign["assignment_name"],
                        opens_at="2026-07-01T00:00:00Z",
                        closes_at=assign["due_date"] + "T23:59:59Z",
                        type="assignment"
                    )
                    session.add(ae)

                # GitHub Activity
                for git in s_data["github_activity"]:
                    ga = GithubActivity(
                        student_id=s_key,
                        repo=git["repo"],
                        commits_today=git["commits_today"],
                        last_commit_at=git["last_commit"],
                        raw_payload=json.dumps(git)
                    )
                    session.add(ga)

                # LeetCode Submissions
                for sub in s_data["leetcode_submissions"]:
                    ls = LeetcodeSubmission(
                        student_id=s_key,
                        problem=sub["problem"],
                        difficulty=sub["difficulty"],
                        time_taken_seconds=sub["time_taken_seconds"],
                        attempts=sub["attempts"],
                        solved_at=sub["solved_at"]
                    )
                    session.add(ls)

                # Resume bullet initial seed
                rb = ResumeBullet(
                    id=f"bullet-{s_key}-1",
                    student_id=s_key,
                    text=f"Built responsive web app features using Python and FastAPI for {s_data['profile']['name']}.",
                    evidence_link="https://github.com/example/project",
                    created_at=datetime.utcnow().isoformat() + "Z",
                    outcome_feedback=None
                )
                session.add(rb)

            session.commit()
            print("Successfully seeded SQLite database zenoai.db via SQLModel.")
    except Exception as sqle:
        print(f"SQLite seeding notice: {sqle}")

    # 2. Seed PostgreSQL database if configured
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "postgresql" not in db_url:
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS moodle_student_profiles (
                student_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                level VARCHAR,
                skills JSONB,
                goal VARCHAR
            );
            
            CREATE TABLE IF NOT EXISTS moodle_quiz_scores (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                subject VARCHAR,
                score INTEGER,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS moodle_assignments (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                assignment_name VARCHAR,
                status VARCHAR,
                due_date VARCHAR
            );
                        
            CREATE TABLE IF NOT EXISTS moodle_programming_progress (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                topic VARCHAR,
                status VARCHAR,
                completion_pct INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS moodle_exam_schedules (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                exam_name VARCHAR,
                date VARCHAR,
                duration_minutes INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS github_activity (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                repo VARCHAR,
                commits_today INTEGER,
                last_commit TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS leetcode_submissions (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR,
                problem VARCHAR,
                difficulty VARCHAR,
                time_taken_seconds INTEGER,
                attempts INTEGER,
                solved_at TIMESTAMP
            );
        """)

        for s_key in ["student_a", "student_b", "student_c"]:
            cur.execute("DELETE FROM moodle_student_profiles WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM moodle_quiz_scores WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM moodle_assignments WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM moodle_programming_progress WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM moodle_exam_schedules WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM github_activity WHERE student_id = %s", (s_key,))
            cur.execute("DELETE FROM leetcode_submissions WHERE student_id = %s", (s_key,))

            s_data = data[s_key]

            cur.execute(
                "INSERT INTO moodle_student_profiles (student_id, name, level, skills, goal) VALUES (%s, %s, %s, %s, %s)",
                (s_key, s_data["profile"]["name"], s_data["profile"]["level"], json.dumps(s_data["profile"]["skills"]), s_data["profile"]["goal"])
            )

            for sub, score in s_data["quiz_scores"].items():
                cur.execute(
                    "INSERT INTO moodle_quiz_scores (student_id, subject, score) VALUES (%s, %s, %s)",
                    (s_key, sub, score)
                )

            for assign in s_data["assignments"]:
                cur.execute(
                    "INSERT INTO moodle_assignments (student_id, assignment_name, status, due_date) VALUES (%s, %s, %s, %s)",
                    (s_key, assign["assignment_name"], assign["status"], assign["due_date"])
                )
            for prog in s_data["programming_progress"]:
                cur.execute(
                    "INSERT INTO moodle_programming_progress (student_id, topic, status, completion_pct) VALUES (%s, %s, %s, %s)",
                    (s_key, prog["topic"], prog["status"], prog["completion_pct"])
                )

            for exam in s_data["exam_schedule"]:
                cur.execute(
                    "INSERT INTO moodle_exam_schedules (student_id, exam_name, date, duration_minutes) VALUES (%s, %s, %s, %s)",
                    (s_key, exam["exam_name"], exam["date"], exam["duration_minutes"])
                )

            for git in s_data["github_activity"]:
                cur.execute(
                    "INSERT INTO github_activity (student_id, repo, commits_today, last_commit) VALUES (%s, %s, %s, %s)",
                    (s_key, git["repo"], git["commits_today"], git["last_commit"])
                )

            for sub in s_data["leetcode_submissions"]:
                cur.execute(
                    "INSERT INTO leetcode_submissions (student_id, problem, difficulty, time_taken_seconds, attempts, solved_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (s_key, sub["problem"], sub["difficulty"], sub["time_taken_seconds"], sub["attempts"], sub["solved_at"])
                )

        conn.commit()
        cur.close()
        conn.close()
        print("Successfully seeded PostgreSQL database tables with idempotent demo history.")
    except Exception as e:
        print(f"PostgreSQL database notice: {e}")

if __name__ == "__main__":
    generated_data = generate_history()
    write_fixtures(generated_data)
    seed_db(generated_data)


