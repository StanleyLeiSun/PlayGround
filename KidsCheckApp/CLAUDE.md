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

**⚠️ 模拟器开发必须使用 `dev` flavor，不能连接线上服务端。** `prod`/`localProd` flavor 的 BASE_URL 指向线上服务器，模拟器连线上会导致新功能因线上未部署而失败，且会污染线上数据。

```bash
# 编译 dev flavor（BASE_URL = http://10.0.2.2:8000，指向本地后端）
./gradlew assembleDevDebug

# 安装到模拟器
adb install -r app/build/outputs/apk/dev/debug/app-dev-debug.apk

# ❌ 永远不要在模拟器上安装 prod flavor
# ./gradlew assembleProdDebug  ← 不要这样做
```

Open in Android Studio, Sync, and run on emulator or device. The emulator uses `10.0.2.2:8000` to reach the local backend; real devices need the LAN IP set in `RetrofitInstance.kt`.

## Architecture

任何服务端、数据库的改变都要向前兼容，确保客户端不升级也可以运行

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

## 上线
- 操作线上服务、版本时要遵守docs\sop中的流程
- 任何数据库操作前先做备份

### 功能自测 Checklist

每个新功能交付前必须按以下维度逐一验证：

- **分支覆盖**：`if/else` 的每个分支都要走到，特别是状态相关的分支（pending vs done、不同 type 等）
- **旧功能回归**：新增数据实体（如 OralRecording）时，必须审核已有操作（undo、delete、list）是否覆盖对新实体的处理
- **前后端校验对齐**：前端先拦（禁用按钮/提示），后端兜底；API 错误信息必须透传给用户，不能吞掉
- **边界数据**：测试数据应包含长标题（20字+）、多标签组合等，及早暴露布局问题

### 已踩过的坑

| 问题 | 根因 | 防范 |
|------|------|------|
| `return@Box` 导致 Compose 闪退 | 在 `if` 块内用 `return@Box` 提前退出，破坏 Compose 组合树 startGroup/endGroup 配对 | 用顶层 `if/else` 互斥渲染替代 `return@Box` |
| 模拟器连了线上服务器 | `assembleDebug` 编译所有 flavor，默认安装了 prod | 模拟器永远用 `assembleDevDebug`（见上方 Android 命令） |
| 新增实体后 undo 不清理 | 只测了正向打卡流程，没回归 undo 路径 | 新增实体时必须检查所有已有操作 |
| API 错误信息被吞 | `catch` 后只返回 null，400 response body 被丢弃 | 所有 API 调用必须解析并透传 `errorBody` 中的 detail |
| Row 布局右侧被挤压 | `weight(1f)` 默认 `fill=true`，标签+积分+删除按钮占位过多 | 用 `weight(1f, fill=false)` + 精简标签文字 |
