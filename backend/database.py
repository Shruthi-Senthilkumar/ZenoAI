import os
import json
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine, Session, select

# SQLite database file URL (Postgres-portable with SQLModel)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zenoai.db")
DATABASE_URL = os.getenv("SQLITE_DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# 1. Students Table
class Student(SQLModel, table=True):
    __tablename__ = "students"
    
    id: str = Field(primary_key=True, description="Student ID e.g. student_a")
    name: str
    target_role: str = Field(default="Software Engineer")
    weekly_hours: int = Field(default=15)
    github_username: Optional[str] = Field(default=None)
    github_token_encrypted: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# 2. Learning Profile Table
class LearningProfile(SQLModel, table=True):
    __tablename__ = "learning_profile"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    subject: str
    avg_score: float = Field(default=0.0)
    trend: str = Field(default="flat")  # "up", "down", "flat"
    last_test: float = Field(default=0.0)
    

# 3. Quiz Scores Table
class QuizScore(SQLModel, table=True):
    __tablename__ = "quiz_scores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    course: str
    quiz: str
    attempt: int = Field(default=1)
    marks: float = Field(default=0.0)
    grade_pct: float = Field(default=0.0)
    duration_seconds: int = Field(default=0)
    missed_topics: str = Field(default="[]")  # JSON string

# 4. Assignments & Events Table
class AssignmentEvent(SQLModel, table=True):
    __tablename__ = "assignments_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    title: str
    opens_at: str
    closes_at: str
    type: str = Field(default="assignment")  # "assignment", "exam"

# 5. GitHub Activity Table
class GithubActivity(SQLModel, table=True):
    __tablename__ = "github_activity"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    repo: str
    commits_today: int = Field(default=0)
    last_commit_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    raw_payload: str = Field(default="{}")  # JSON string

# 6. LeetCode Submissions Table
class LeetcodeSubmission(SQLModel, table=True):
    __tablename__ = "leetcode_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    problem: str
    difficulty: str = Field(default="Easy")
    time_taken_seconds: int = Field(default=0)
    attempts: int = Field(default=1)
    solved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# 7. Connector Capabilities Table
class ConnectorCapability(SQLModel, table=True):
    __tablename__ = "connector_capabilities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    capability: str
    available: bool = Field(default=True)

# 8. Jobs Cache Table
class JobCache(SQLModel, table=True):
    __tablename__ = "jobs_cache"
    
    id: str = Field(primary_key=True)
    title: str
    company: str
    match_pct: float = Field(default=0.0)
    missing_skills: str = Field(default="[]")  # JSON string
    source: str = Field(default="Adzuna+JSearch")
    fetched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

# 9. Resume Bullets Table
class ResumeBullet(SQLModel, table=True):
    __tablename__ = "resume_bullets"
    
    id: str = Field(primary_key=True)
    student_id: str = Field(index=True)
    text: str
    evidence_link: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    outcome_feedback: Optional[str] = Field(default=None)  # "yes", "no", "somewhat"


# Initialize database tables
def init_db():
    SQLModel.metadata.create_all(engine)

# Shared Student Insert Helper exposed to Shruthi's intake flow
def create_or_update_student(
    student_id: str,
    name: str,
    target_role: str = "Software Engineer",
    weekly_hours: int = 15,
    github_username: Optional[str] = None
) -> Student:
    with Session(engine) as session:
        student = session.get(Student, student_id)
        if not student:
            student = Student(
                id=student_id,
                name=name,
                target_role=target_role,
                weekly_hours=weekly_hours,
                github_username=github_username
            )
            session.add(student)
        else:
            student.name = name
            student.target_role = target_role
            student.weekly_hours = weekly_hours
            if github_username:
                student.github_username = github_username
            session.add(student)
        session.commit()
        session.refresh(student)
        return student

def get_session():
    with Session(engine) as session:
        yield session
