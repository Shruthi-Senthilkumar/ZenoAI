import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

class MoodleConnector:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")

    def _get_connection(self):
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        return psycopg2.connect(self.db_url)

    def _query_db(self, query: str, params: tuple, fetch_one: bool = False):
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch_one:
                    row = cur.fetchone()
                    return dict(row) if row else None
                else:
                    rows = cur.fetchall()
                    return [dict(r) for r in rows] if rows else []
        except Exception as e:
            # Print to stdout/stderr for logging/visibility but allow the caller to fallback
            print(f"Database query error: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    def get_student_profile(self, student_id: str) -> dict:
        try:
            row = self._query_db(
                "SELECT name, level, skills, goal FROM moodle_student_profiles WHERE student_id = %s",
                (student_id,),
                fetch_one=True
            )
            if row:
                if isinstance(row.get("skills"), str):
                    try:
                        row["skills"] = json.loads(row["skills"])
                    except Exception:
                        row["skills"] = [s.strip() for s in row["skills"].split(",") if s.strip()]
                return row
        except Exception:
            pass
            
        return {
            "name": student_id.replace("student_", "").capitalize(),
            "level": "Beginner",
            "skills": ["Python"],
            "goal": "Learn programming"
        }

    def get_quiz_scores(self, student_id: str) -> dict:
        try:
            rows = self._query_db(
                "SELECT subject, score FROM moodle_quiz_scores WHERE student_id = %s",
                (student_id,)
            )
            if rows:
                return {r["subject"]: r["score"] for r in rows}
        except Exception:
            pass
            
        return {"DSA": 70, "Python": 75, "AI": 68}

    def get_assignments(self, student_id: str) -> list[dict]:
        try:
            return self._query_db(
                "SELECT assignment_name, status, due_date FROM moodle_assignments WHERE student_id = %s",
                (student_id,)
            )
        except Exception:
            pass
        return []

    def get_programming_progress(self, student_id: str) -> list[dict]:
        try:
            return self._query_db(
                "SELECT topic, status, completion_pct FROM moodle_programming_progress WHERE student_id = %s",
                (student_id,)
            )
        except Exception:
            pass
        return []

    def get_exam_schedule(self, student_id: str) -> list[dict]:
        try:
            return self._query_db(
                "SELECT exam_name, date, duration_minutes FROM moodle_exam_schedules WHERE student_id = %s",
                (student_id,)
            )
        except Exception:
            pass
        return []