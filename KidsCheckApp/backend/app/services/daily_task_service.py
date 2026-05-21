from datetime import datetime, date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DailyTask, TaskTemplate, ConditionalTask, TaskStatus, TaskType,
)
from app.services import points_service


async def generate_daily_tasks(db: AsyncSession, child_id: int, target_date: date) -> list[DailyTask]:
    """Generate daily tasks from templates for a given child and date."""
    # Get existing tasks for this child and date
    existing_result = await db.execute(
        select(DailyTask).where(
            DailyTask.child_id == child_id,
            func.date(DailyTask.date) == target_date,
        )
    )
    existing_tasks = list(existing_result.scalars().all())
    existing_template_ids = {t.source_template_id for t in existing_tasks if t.source_template_id}

    weekday = target_date.isoweekday()  # 1=Monday, 7=Sunday

    result = await db.execute(
        select(TaskTemplate)
        .where(TaskTemplate.child_id == child_id, TaskTemplate.weekday == weekday)
        .order_by(TaskTemplate.sort_order)
    )
    templates = result.scalars().all()

    new_tasks = []
    for t in templates:
        if t.id in existing_template_ids:
            continue
        task = DailyTask(
            child_id=child_id,
            date=datetime.combine(target_date, datetime.min.time()),
            source_template_id=t.id,
            title=t.title,
            type=TaskType(t.type.value) if hasattr(t.type, 'value') else TaskType(t.type),
            points=t.points,
            description=t.description,
            status=TaskStatus.pending,
            is_conditional=False,
        )
        db.add(task)
        new_tasks.append(task)

    if new_tasks:
        await db.flush()
        for t in new_tasks:
            await db.refresh(t)

    return existing_tasks + new_tasks


async def check_and_insert_conditional_tasks(db: AsyncSession, child_id: int, target_date: date):
    """Insert conditional tasks if all required tasks are done."""
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.child_id == child_id,
            func.date(DailyTask.date) == target_date,
            DailyTask.is_conditional == False,
        )
    )
    required_tasks = result.scalars().all()

    if not required_tasks:
        return

    all_done = all(t.status == TaskStatus.done for t in required_tasks)
    if not all_done:
        return

    # Check if conditional tasks already inserted
    existing_cond = await db.execute(
        select(DailyTask).where(
            DailyTask.child_id == child_id,
            func.date(DailyTask.date) == target_date,
            DailyTask.is_conditional == True,
        )
    )
    if existing_cond.scalars().first():
        return

    # Insert conditional tasks
    cond_result = await db.execute(
        select(ConditionalTask).where(ConditionalTask.child_id == child_id)
    )
    cond_templates = cond_result.scalars().all()

    weekday = target_date.isoweekday()
    for ct in cond_templates:
        if ct.weekdays:
            allowed = [int(d) for d in ct.weekdays.split(",") if d.strip()]
            if weekday not in allowed:
                continue
        task = DailyTask(
            child_id=child_id,
            date=datetime.combine(target_date, datetime.min.time()),
            source_template_id=ct.id,
            title=ct.title,
            type=TaskType(ct.type.value) if hasattr(ct.type, 'value') else TaskType(ct.type),
            points=ct.points,
            status=TaskStatus.pending,
            is_conditional=True,
        )
        db.add(task)

    await db.flush()


async def get_daily_tasks(db: AsyncSession, child_id: int, target_date: date) -> list[DailyTask]:
    """Get daily tasks, generating from templates if needed."""
    # Always check for new templates to generate
    await generate_daily_tasks(db, child_id, target_date)

    result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            func.date(DailyTask.date) == target_date,
        )
        .order_by(DailyTask.is_conditional, DailyTask.id)
    )
    return list(result.scalars().all())


async def check_in_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    has_photo: bool = False,
) -> DailyTask:
    """Mark a daily task as done."""
    result = await db.execute(select(DailyTask).where(DailyTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("Task not found")
    if task.status == TaskStatus.done:
        raise ValueError("Already completed")

    # Validate photo requirement for written tasks
    if task.type == TaskType.written and not has_photo:
        raise ValueError("Photo required for written tasks")

    task.status = TaskStatus.done
    task.completed_at = datetime.utcnow()
    task.completed_by = user_id
    await db.flush()

    # Award points
    await points_service.award_points(db, task.child_id, task.points, task.id)

    # Check if all required done, insert conditional tasks
    target_date = task.date.date() if hasattr(task.date, 'date') else task.date
    await check_and_insert_conditional_tasks(db, task.child_id, target_date)

    await db.refresh(task)
    return task
