"""ZenoAI backend entrypoint.
Mounts every router in backend/routes/ onto a single FastAPI app so
Thaariha's Next.js client (and `/docs`) has one process to talk to.
Run with: uvicorn main:app --reload
"""
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import (
    auth,
    chat,
    dashboard,
    feedback,
    intake,
    jobs,
    leetcode,
    notifications,
    push,
    quiz,
    roadmap,
    struggle,
    tasks,
)
from backend.seed import generate_history, seed_db, write_fixtures

load_dotenv()

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
app.include_router(chat.router)
app.include_router(leetcode.router)
app.include_router(jobs.router)
app.include_router(auth.router)


async def github_poll_loop():
    """Daily GitHub activity poll, runs inside the FastAPI process
    (Integration Spec §6.2/§6.3) — no Celery, no external cron."""
    while True:
        try:
            print("Background GitHub poll: checking connected students...")
        except Exception as e:
            print(f"Error in github_poll_loop: {e}")
        await asyncio.sleep(86400)


@app.on_event("startup")
async def start_background_loops():
    try:
        init_db()
        data = generate_history()
        write_fixtures(data)
        seed_db(data)
    except Exception as e:
        print(f"Startup DB init notice: {e}")
    asyncio.create_task(github_poll_loop())


@app.get("/")
def read_root():
    return {"message": "Welcome to ZenoAI API", "docs": "/docs", "status": "online"}