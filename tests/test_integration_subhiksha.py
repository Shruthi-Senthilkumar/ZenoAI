import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select, delete

from backend.main import app
from backend.database import (
    init_db, engine, Student, LearningProfile, QuizScore,
    AssignmentEvent, GithubActivity, LeetcodeSubmission,
    ConnectorCapability, JobCache, ResumeBullet, create_or_update_student
)
from backend.connectors.lms_connector import get_connector

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db_initialized():
    init_db()

def test_database_initialization_and_student_helper():
    init_db()
    student = create_or_update_student(
        student_id="student_test",
        name="Test Student",
        target_role="Backend Developer",
        weekly_hours=20,
        github_username="test_dev"
    )
    assert student.id == "student_test"
    assert student.name == "Test Student"
    assert student.target_role == "Backend Developer"
    
    with Session(engine) as session:
        db_student = session.get(Student, "student_test")
        assert db_student is not None
        assert db_student.github_username == "test_dev"

def test_job_feed_deduplication_and_caching():
    response = client.get("/jobs?student_id=student_a")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    
    # Check deduplication (TechCorp Frontend Engineer Intern appears once)
    techcorp_jobs = [j for j in jobs if j["company"] == "TechCorp" and j["title"] == "Frontend Engineer Intern"]
    assert len(techcorp_jobs) == 1
    
    # Check DB caching
    with Session(engine) as session:
        cached_jobs = session.exec(select(JobCache)).all()
        assert len(cached_jobs) >= len(jobs)


def test_resume_bullet_feedback_persistence():
    with Session(engine) as session:
        session.exec(delete(ResumeBullet).where(ResumeBullet.id == "bullet-test-101"))
        session.commit()

        bullet = ResumeBullet(
            id="bullet-test-101",
            student_id="student_a",
            text="Optimized database indexing for FastAPI backend.",
            outcome_feedback=None
        )
        session.add(bullet)
        session.commit()

    response = client.post("/resume/bullets/bullet-test-101/feedback", json={"outcome": "yes"})
    assert response.status_code == 200
    assert response.json()["outcome"] == "yes"

    with Session(engine) as session:
        session.exec(delete(ResumeBullet).where(ResumeBullet.id == "bullet-test-101"))
        session.commit()