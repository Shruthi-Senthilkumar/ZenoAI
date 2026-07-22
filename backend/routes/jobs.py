import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from backend.database import engine, JobCache, Student

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobMatch(BaseModel):
    id: str
    title: str
    company: str
    match_pct: float
    missing_skills: List[str]
    source: str

# Curated job feed source (Adzuna + JSearch mock feed)
MOCK_JOB_LISTINGS = [
    {
        "id": "job-101",
        "title": "Frontend Engineer Intern",
        "company": "TechCorp",
        "required_skills": ["Python", "React", "TypeScript", "TailwindCSS"],
        "source": "JSearch"
    },
    {
        "id": "job-102",
        "title": "Backend Developer Intern",
        "company": "DataScale Inc",
        "required_skills": ["Python", "SQL", "FastAPI", "Docker", "PostgreSQL"],
        "source": "Adzuna"
    },
    {
        "id": "job-103",
        "title": "Full Stack Intern",
        "company": "CloudNative Labs",
        "required_skills": ["Python", "DSA", "SQL", "Git"],
        "source": "JSearch"
    },
    {
        "id": "job-104",
        "title": "Frontend Engineer Intern",
        "company": "TechCorp", # Duplicate to test deduplication
        "required_skills": ["Python", "React", "TypeScript"],
        "source": "Adzuna"
    }
]

def calculate_match(student_skills: List[str], required_skills: List[str]):
    student_skills_lower = set(s.lower() for s in student_skills)
    matched = [s for s in required_skills if s.lower() in student_skills_lower]
    missing = [s for s in required_skills if s.lower() not in student_skills_lower]
    
    pct = round((len(matched) / len(required_skills)) * 100, 1) if required_skills else 100.0
    return pct, missing

@router.get("", response_model=List[JobMatch])
@router.get("/", response_model=List[JobMatch])
def get_job_listings(student_id: Optional[str] = Query("student_a", description="Student ID to compute skill match against")):
    # 1. Fetch student skills if present in DB
    student_skills = ["Python", "DSA", "SQL"]
    try:
        with Session(engine) as session:
            student = session.get(Student, student_id)
            if student:
                # Basic skills mapping
                student_skills = ["Python", "DSA", "SQL", "Git"]
    except Exception:
        pass

    # 2. Deduplicate listings by title + company
    seen_keys = set()
    deduped = []
    
    for job in MOCK_JOB_LISTINGS:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        
        pct, missing = calculate_match(student_skills, job["required_skills"])
        
        job_match = JobMatch(
            id=job["id"],
            title=job["title"],
            company=job["company"],
            match_pct=pct,
            missing_skills=missing,
            source=job["source"]
        )
        deduped.append(job_match)

    # 3. Cache to jobs_cache table
    try:
        with Session(engine) as session:
            for item in deduped:
                cached = session.get(JobCache, item.id)
                if not cached:
                    cached = JobCache(
                        id=item.id,
                        title=item.title,
                        company=item.company,
                        match_pct=item.match_pct,
                        missing_skills=json.dumps(item.missing_skills),
                        source=item.source,
                        fetched_at=datetime.utcnow().isoformat() + "Z"
                    )
                    session.add(cached)
                else:
                    cached.match_pct = item.match_pct
                    cached.missing_skills = json.dumps(item.missing_skills)
                    session.add(cached)
            session.commit()
    except Exception as e:
        print(f"Error caching jobs to database: {e}")

    return deduped
