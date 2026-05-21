from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import UPLOAD_DIR
from app.routers import auth, children, templates, conditional_tasks, daily_tasks, progress, points, rewards, action_logs, insights, app_version
from app.services.daily_task_service import generate_daily_tasks
from app.database import async_session

scheduler = AsyncIOScheduler()


async def scheduled_daily_generation():
    """Generate daily tasks for all children at 00:00."""
    from sqlalchemy import select
    from app.models.models import Child
    from datetime import date

    async with async_session() as db:
        result = await db.execute(select(Child))
        children_list = result.scalars().all()
        for child in children_list:
            await generate_daily_tasks(db, child.id, date.today())
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create upload dir and start scheduler
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    scheduler.add_job(scheduled_daily_generation, "cron", hour=0, minute=0, timezone="Asia/Shanghai")
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="KidsCheck API",
    description="家庭学习打卡助手",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files for photo serving
app.mount("/photos", StaticFiles(directory=str(UPLOAD_DIR)), name="photos")

# Register routers
app.include_router(auth.router)
app.include_router(children.router)
app.include_router(templates.router)
app.include_router(conditional_tasks.router)
app.include_router(daily_tasks.router)
app.include_router(progress.router)
app.include_router(points.router)
app.include_router(rewards.router)
app.include_router(action_logs.router)
app.include_router(insights.router)
app.include_router(app_version.router)


@app.get("/")
async def root():
    return {"message": "KidsCheck API", "version": "1.0.0"}
