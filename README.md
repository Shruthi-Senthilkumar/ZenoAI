![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Hackathon](https://img.shields.io/badge/Hackathon-2026-orange)
# 🎓 ZenoAI

> **Your AI Student Mentor for Academic & Career Success**
>
> *"The AI buddy that tracks your exams and your commits — so you never have to choose which future to work on today."*

---

## 🚀 Overview

**ZenoAI** is an AI-powered student mentor that unifies **academic learning** and **career preparation** into one intelligent platform.

Unlike traditional learning management systems or coding trackers, ZenoAI combines data from **college LMS**, **GitHub**, and **LeetCode** to understand a student's overall progress and generate personalized guidance.

It doesn't just tell students **how they are doing**—it tells them **what to do next, why it matters, and when to do it.**

---

## ✨ Features

### 🎯 Personalized AI Roadmap
- Generates daily academic & career tasks
- Prerequisite-aware learning using Skill DAG
- Dynamic planning based on student performance

### 📚 LMS Performance Analysis
- Quiz score tracking
- Assignment monitoring
- Attendance analysis
- Exam schedule integration
- Future-ready Moodle API Connector

### 💻 Career Progress Tracking
- GitHub activity analysis
- LeetCode progress monitoring
- Internship recommendations
- Resume bullet generation

### 🤖 AI Mentor
- Personalized study guidance
- Goal planning
- Adaptive learning recommendations
- Intelligent Q&A assistant

### 📈 Readiness Dashboard
Separate readiness scores for

- Academic Readiness
- Career Readiness

with trend analysis and personalized recommendations.

### ⚡ Struggle Detection
Automatically detects learning gaps and recommends:

- Quick revision plans
- Practice quizzes
- Focus sessions
- Personalized interventions

---

# 🏗 Architecture

```
                LMS
                 │
         LMS Connector
                 │
GitHub ──────────┼────────── LeetCode
                 │
      Student Learning Profile
                 │
        AI Decision Engine
        ├── Roadmap Generator
        ├── Readiness Engine
        ├── Struggle Detector
        ├── Quiz Generator
        └── Mentor AI
                 │
           FastAPI Backend
                 │
       Supabase PostgreSQL
                 │
        Next.js Frontend
```

---

# 🛠 Tech Stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Zustand
- SWR
- Recharts

## Backend

- FastAPI
- Python
- SQLModel
- Pydantic
- NetworkX

## AI

- GROQ API
- Llama 3.3 70B
- Ollama (Fallback)

## Database

- Supabase PostgreSQL

## Integrations

- Moodle LMS
- GitHub API
- LeetCode
- Adzuna API
- JSearch API

---

# 📂 Project Structure

```
ZenoAI
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── lib/
│
├── backend/
│   ├── routes/
│   ├── logic/
│   ├── connectors/
│   ├── llm/
│   ├── db/
│   └── scheduler/
│
└── docs/
```

---

# 🔄 Workflow

```
Student
    │
    ▼
Adaptive Intake
    │
    ▼
LMS + GitHub + LeetCode
    │
    ▼
Student Learning Profile
    │
    ▼
AI Decision Engine
    │
    ├── Roadmap
    ├── Readiness
    ├── Tasks
    ├── Mentor AI
    └── Quiz Generator
    │
    ▼
Next.js Dashboard
```

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/<username>/ZenoAI.git
cd ZenoAI
```

---

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on

```
http://localhost:8000
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on

```
http://localhost:3000
```

---

# 🌟 Future Scope

- Real Moodle API Integration
- Multi-LMS Support
- Push Notifications
- Mobile Application
- AI Interview Preparation
- Voice Mentor
- Predictive Performance Analytics
- Faculty Dashboard
- Parent Dashboard

---

# 👥 Team

| Name | Responsibility |
|-------|----------------|
| **Shruthi** | Backend, AI Engine, Roadmap, Mentor AI |
| **Subhiksha** | LMS Connector, Database, API Integrations |
| **Thaariha** | Frontend, UI/UX, Dashboard |

---

# 💡 Why ZenoAI?

Students today manage academics and career preparation using disconnected platforms.

**ZenoAI bridges this gap by becoming one intelligent mentor that understands both.**

Instead of asking

> *"What should I study today?"*

ZenoAI answers

> **"Here's what you should do next, why it matters, and how it improves both your semester and your career."**

---

## ⭐ If you like this project, consider giving it a star!
