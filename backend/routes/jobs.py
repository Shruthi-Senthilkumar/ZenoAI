"""GET /jobs — internship/job listings matched against the student's
real skill evidence.

Two real, distinct pieces of work happened here (previously both were
hardcoded):

1. Live listings: calls the real Adzuna Job Search API (free tier,
   ~1000 calls/month) when ADZUNA_APP_ID/ADZUNA_APP_KEY are set in
   .env. Falls back to MOCK_JOB_LISTINGS — same graceful-degradation
   shape as every other external call in this codebase — when the
   keys aren't configured or the request fails, so the page never
   goes blank.

2. Skill matching: student_skills used to be a hardcoded list
   ("Python, DSA, SQL, Git") returned for literally every student
   regardless of who asked. Now pulled from the student's real,
   evaluated intake profile (backend/logic/intake.py) — topics scored
   "intermediate" or "advanced" in topic_levels, which is itself
   evaluated from the student's actual diagnostic answers, not
   self-reported.

Known limitation, flagged not fixed: Adzuna doesn't return structured
per-listing required-skill lists (unlike a hypothetical JSearch
integration might) — only free-text titles/descriptions. Matching here
is a real but simple heuristic: checks whether known tech-skill
keywords appear in the listing's title+description text. JSearch
(RapidAPI) integration itself is not implemented — Adzuna alone covers
this route for now.
"""
import json
import os
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database import JobCache, Student, engine

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobMatch(BaseModel):
    id: str
    title: str
    company: str
    match_pct: float
    missing_skills: List[str]
    source: str


# Fallback only — used when Adzuna isn't configured or the live call fails.
MOCK_JOB_LISTINGS = [
    {
        "id": "job-101",
        "title": "Frontend Engineer Intern",
        "company": "TechCorp",
        "required_skills": ["Python", "React", "TypeScript", "TailwindCSS"],
        "source": "JSearch",
    },
    {
        "id": "job-102",
        "title": "Backend Developer Intern",
        "company": "DataScale Inc",
        "required_skills": ["Python", "SQL", "FastAPI", "Docker", "PostgreSQL"],
        "source": "Adzuna",
    },
    {
        "id": "job-103",
        "title": "Full Stack Intern",
        "company": "CloudNative Labs",
        "required_skills": ["Python", "DSA", "SQL", "Git"],
        "source": "JSearch",
    },
    {
        "id": "job-104",
        "title": "Frontend Engineer Intern",
        "company": "TechCorp",  # Duplicate to test deduplication
        "required_skills": ["Python", "React", "TypeScript"],
        "source": "Adzuna",
    },
]

# Keyword vocabulary checked against real Adzuna listing text, since Adzuna
# gives free-text descriptions, not structured skill lists. Deliberately
# small and tech-generic rather than trying to enumerate every possible
# skill — precision over recall for a heuristic like this.
SKILL_KEYWORDS = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "React", "Node",
    "FastAPI", "Django", "Docker", "Kubernetes", "AWS", "Git", "DSA",
    "Machine Learning", "Linux", "REST", "API", "PostgreSQL", "MongoDB",
]

ROLE_TO_SEARCH_QUERY = {
    "SDE": "software engineer intern",
    "Data": "data analyst intern",
    "Core": "engineer intern",
}

# Maps DAG-style topic names (from intake's topic_levels) to a
# human-readable skill keyword worth checking for in job listings.
TOPIC_TO_SKILL_KEYWORD = {
    "python-basics": "Python",
    "arrays": "DSA",
    "recursion": "DSA",
    "dynamic-programming": "DSA",
    "linear-algebra": "Machine Learning",
    "sql": "SQL",
    "system-design-basics": "REST",
}


def get_student_skills(student_id: str) -> List[str]:
    """Real skills, not a hardcoded list — pulled from the student's
    actual evaluated intake profile. A topic only counts once its
    diagnostic answer was judged "intermediate" or "advanced"
    (backend/logic/intake.py's extraction), not merely asked about."""
    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        if student is None:
            return []

        skills = set()
        if student.topic_levels_json:
            try:
                topic_levels = json.loads(student.topic_levels_json)
            except json.JSONDecodeError:
                topic_levels = {}
            for topic, level in topic_levels.items():
                if level in ("intermediate", "advanced"):
                    keyword = TOPIC_TO_SKILL_KEYWORD.get(topic)
                    if keyword:
                        skills.add(keyword)

        return list(skills)


def calculate_match(student_skills: List[str], required_skills: List[str]):
    student_skills_lower = set(s.lower() for s in student_skills)
    matched = [s for s in required_skills if s.lower() in student_skills_lower]
    missing = [s for s in required_skills if s.lower() not in student_skills_lower]

    pct = round((len(matched) / len(required_skills)) * 100, 1) if required_skills else 100.0
    return pct, missing


def fetch_adzuna_listings(target_role: str) -> Optional[list[dict]]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return None

    query = ROLE_TO_SEARCH_QUERY.get(target_role, "software engineer intern")
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(
                "https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": query,
                    "results_per_page": 10,
                    "content-type": "application/json",
                },
            )
            if response.status_code != 200:
                return None
            results = response.json().get("results", [])
    except Exception:
        return None

    listings = []
    for job in results:
        title = job.get("title", "").strip()
        company = (job.get("company") or {}).get("display_name", "Unknown")
        description = job.get("description", "")
        text = f"{title} {description}"
        required_skills = [kw for kw in SKILL_KEYWORDS if kw.lower() in text.lower()]
        listings.append(
            {
                "id": job.get("id", f"adzuna-{len(listings)}"),
                "title": title,
                "company": company,
                "required_skills": required_skills,
                "source": "Adzuna",
            }
        )
    return listings


@router.get("", response_model=List[JobMatch])
@router.get("/", response_model=List[JobMatch])
def get_job_listings(student_id: Optional[str] = Query("student_a", description="Student ID to compute skill match against")):
    student_skills = get_student_skills(student_id)

    with Session(engine) as session:
        student = session.exec(select(Student).where(Student.id == student_id)).first()
        target_role = student.target_role if student else "SDE"
        # Map the free-text target_role stored on Student back to the
        # SDE/Data/Core categories the search-query map expects.
        role_key = "SDE"
        for key in ("SDE", "Data", "Core"):
            if key.lower() in (target_role or "").lower():
                role_key = key
                break

    listings = fetch_adzuna_listings(role_key)
    if listings is None:
        listings = MOCK_JOB_LISTINGS

    seen_keys = set()
    deduped = []

    for job in listings:
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
            source=job["source"],
        )
        deduped.append(job_match)

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
                        fetched_at=datetime.utcnow().isoformat() + "Z",
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