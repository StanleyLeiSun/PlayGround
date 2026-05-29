from datetime import date, timedelta, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import User, DailyTask, TaskStatus, TaskType
from app.schemas.schemas import InsightsResponse, DailyStatItem, TaskStatItem

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/{child_id}", response_model=InsightsResponse)
async def get_insights(
    child_id: int,
    period: str = Query("week", pattern="^(week|last_week|month)$"),
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "last_week":
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    else:  # month
        start_date = today.replace(day=1)
        end_date = today

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    result = await db.execute(
        select(
            func.date(DailyTask.date).label("day"),
            func.count(DailyTask.id).label("total"),
            func.sum(case((DailyTask.status == TaskStatus.done, 1), else_=0)).label("completed"),
            func.sum(case((DailyTask.status == TaskStatus.done, DailyTask.points), else_=0)).label("points"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.date >= start_dt,
            DailyTask.date <= end_dt,
        )
        .group_by(func.date(DailyTask.date))
        .order_by(func.date(DailyTask.date))
    )
    rows = result.all()

    daily_stats = []
    total_tasks = 0
    completed_tasks = 0
    total_points = 0
    for row in rows:
        day_str = str(row.day)
        total = int(row.total)
        completed = int(row.completed)
        points = int(row.points)
        daily_stats.append(DailyStatItem(date=day_str, total=total, completed=completed, points=points))
        total_tasks += total
        completed_tasks += completed
        total_points += points

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    # Task stats: group by title, count completed days and total days
    task_result = await db.execute(
        select(
            DailyTask.title,
            func.count(DailyTask.id).label("total"),
            func.sum(case((DailyTask.status == TaskStatus.done, 1), else_=0)).label("completed"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.date >= start_dt,
            DailyTask.date <= end_dt,
        )
        .group_by(DailyTask.title)
        .order_by(func.sum(case((DailyTask.status == TaskStatus.done, 1), else_=0)).desc())
    )
    task_stats = []
    for row in task_result.all():
        title = row[0]
        total = int(row[1])
        completed = int(row[2])
        ratio = round(completed / total, 3) if total > 0 else 0.0
        task_stats.append(TaskStatItem(title=title, completed=completed, total=total, ratio=ratio))

    # Streak: consecutive days with all tasks completed (from today backwards)
    streak = 0
    check_date = today
    while True:
        check_dt = datetime.combine(check_date, datetime.min.time())
        day_result = await db.execute(
            select(
                func.count(DailyTask.id).label("total"),
                func.sum(case((DailyTask.status == TaskStatus.done, 1), else_=0)).label("completed"),
            )
            .where(
                DailyTask.child_id == child_id,
                func.date(DailyTask.date) == check_date,
            )
        )
        day_row = day_result.one()
        day_total = int(day_row.total) if day_row.total else 0
        day_completed = int(day_row.completed) if day_row.completed else 0

        if day_total == 0 or day_completed < day_total:
            break
        streak += 1
        check_date -= timedelta(days=1)
        if streak > 365:
            break

    return InsightsResponse(
        child_id=child_id,
        period=period,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=round(completion_rate, 1),
        total_points_earned=total_points,
        daily_stats=daily_stats,
        task_stats=task_stats,
        streak=streak,
    )
