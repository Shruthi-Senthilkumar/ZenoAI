"""ZenoAI backend entrypoint.

Mounts every router in backend/routes/ onto a single FastAPI app so
Thaariha's Next.js client (and `/docs`) has one process to talk to.
Run with: uvicorn main:app --reload

NOTE: `chat` router is wired in here as it's built (consolidated fix
item 7) — not present yet on this commit.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    dashboard,
    feedback,
    intake,
    notifications,
    push,
    quiz,
    roadmap,
    struggle,
    tasks,
)

app = FastAPI(title="ZenoAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(feedback.router)
app.include_router(intake.router)
app.include_router(notifications.router)
app.include_router(push.router)
app.include_router(quiz.router)
app.include_router(roadmap.router)
app.include_router(struggle.router)
app.include_router(tasks.router)
