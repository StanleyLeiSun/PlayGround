# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KidsCheck is a family learning check-in app. Parents set daily tasks remotely, grandparents supervise and photograph completion on-site, and kids earn points/rewards. Two components: a Python/FastAPI backend and an Android (Kotlin/Jetpack Compose) client.

## Commands

### Backend (run from `backend/`)

```bash
# One-shot dev server (creates venv, installs deps, runs migrations, starts uvicorn)
./scripts/dev.sh            # macOS/Linux
.\scripts\dev.ps1           # Windows PowerShell

# Manual steps
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
./.venv/bin/python -m pytest

# Run a single test file or test
./.venv/bin/python -m pytest tests/test_daily_tasks.py
./.venv/bin/python -m pytest tests/test_daily_tasks.py::test_name -v

# Create a new migration
./.venv/bin/python -m alembic revision --autogenerate -m "description"
```

### Android (run from `android/`)

Open in Android Studio, Sync, and run on emulator or device. The emulator uses `10.0.2.2:8000` to reach the local backend; real devices need the LAN IP set in `RetrofitInstance.kt`.

## Architecture

### Backend (`backend/`)

FastAPI async app with SQLAlchemy 2.0 async ORM (aiosqlite for SQLite, asyncpg for Postgres).

- `app/main.py` — FastAPI app, lifespan (APScheduler for daily task generation at midnight CST), router registration
- `app/config.py` — env-driven config (DATABASE_URL, JWT, LLM, upload dir)
- `app/database.py` — engine, session factory, `get_db` dependency
- `app/models/models.py` — all SQLAlchemy models (User, Child, TaskTemplate, ConditionalTask, DailyTask, CheckInPhoto, PointAccount, PointTransaction, Reward, RewardRedemption, ActionLog)
- `app/schemas/schemas.py` — Pydantic request/response schemas
- `app/routers/` — one router per domain: auth, children, templates, conditional_tasks, daily_tasks, progress, points, rewards, action_logs
- `app/services/` — business logic layer called by routers (daily_task_service, points_service, template_service, reward_service, action_log_service, auth_service, photo_service, voice_service)
- `app/middleware/auth.py` — JWT auth: `get_current_user`, `require_parent` dependencies
- `alembic/` — migrations (single initial migration creates all tables and seeds preset users/children)

Key patterns:
- Routers depend on `get_db` (yields an AsyncSession that auto-commits or rolls back)
- Two user roles: `parent` (full CRUD on templates/rewards) and `grandparent` (check-in/view only)
- Daily tasks are generated from TaskTemplates (by weekday) + ConditionalTasks (unlocked when all required done)
- Photos stored at `uploads/photos/{child_id}/{date}/{uuid}.jpg`, served via static mount at `/photos`

### Android (`android/`)

Kotlin, Jetpack Compose, single-activity architecture.

- `data/api/ApiService.kt` — Retrofit interface mirroring backend endpoints
- `data/api/RetrofitInstance.kt` — base URL and OkHttp setup (auth interceptor via TokenManager)
- `data/model/Models.kt` — data classes matching API schemas
- `data/local/` — Room database for offline task caching
- `ui/screens/` — Compose screens: auth/LoginScreen, home/MainScreen + TaskListScreen, template/TemplateManagementScreen, progress/ProgressScreen, rewards/RewardsScreen, mine/MineScreen
- `util/TokenManager.kt` — DataStore-based JWT persistence
- `util/PhotoCompressor.kt` — image compression before upload

### Testing

Backend tests use pytest-asyncio with an in-process ASGI test client (httpx). A separate SQLite DB (`test_kidscheck.db`) is created/dropped per test via fixtures in `conftest.py`. The app's `get_db` dependency is overridden to point at the test DB.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| DATABASE_URL | sqlite+aiosqlite:///./kidscheck.db | DB connection string |
| JWT_SECRET | (hardcoded dev key) | Token signing |
| UPLOAD_DIR | uploads/photos | Photo storage path |
| LLM_API_KEY | (empty) | For voice intent parsing (Qwen via DashScope) |
