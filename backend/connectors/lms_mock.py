import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

def load_json(student_id: str, filename: str):
    path = FIXTURES_DIR / student_id / filename
    return json.loads(path.read_text())

class MockConnector:
    def get_student_profile(self, student_id):
        return load_json(student_id, "student_profile.json")

    def get_quiz_scores(self, student_id):
        return load_json(student_id, "quiz_scores.json")

    def get_assignments(self, student_id):
        return load_json(student_id, "assignments.json")

    def get_programming_progress(self, student_id):
        return load_json(student_id, "programming_progress.json")

    def get_exam_schedule(self, student_id):
        return load_json(student_id, "exam_schedule.json")

    def get_attendance(self, student_id):
        # 1. Check cached capabilities table / fixture check
        try:
            from backend.database import engine, ConnectorCapability
            from sqlmodel import Session, select
            with Session(engine) as session:
                cap = session.exec(
                    select(ConnectorCapability).where(
                        ConnectorCapability.student_id == student_id,
                        ConnectorCapability.capability == "attendance"
                    )
                ).first()
                if cap and not cap.available:
                    return {"status": "unavailable", "reason": "endpoint_not_exposed", "attendance_pct": None}
        except Exception:
            pass

        # 2. Try loading attendance fixture
        try:
            data = load_json(student_id, "attendance.json")
            if data.get("status") == "unavailable" or data.get("attendance_pct") is None and "percentage" not in data:
                return {"status": "unavailable", "reason": "endpoint_not_exposed", "attendance_pct": None}
            pct = data.get("percentage") if "percentage" in data else data.get("attendance_pct")
            return {"status": "ok", "attendance_pct": pct}
        except FileNotFoundError:
            # Cache unavailable capability
            try:
                from backend.database import engine, ConnectorCapability
                from sqlmodel import Session
                with Session(engine) as session:
                    cap = ConnectorCapability(student_id=student_id, capability="attendance", available=False)
                    session.add(cap)
                    session.commit()
            except Exception:
                pass
            return {"status": "unavailable", "reason": "endpoint_not_exposed", "attendance_pct": None}
