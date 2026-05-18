"""Tests for daily task generation: scheduled, fallback, idempotency, conditional trigger."""
import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DailyTask, TaskTemplate, TaskType, TaskStatus, ConditionalTask
from app.services.daily_task_service import generate_daily_tasks, get_daily_tasks, check_and_insert_conditional_tasks
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_generate_from_templates(db: AsyncSession, seed_data):
    """Normal daily generation creates tasks from matching weekday templates."""
    child = seed_data["luobo"]
    # Create templates for Monday (weekday=1)
    for title in ["数学口算", "语文抄写"]:
        t = TaskTemplate(child_id=child.id, weekday=1, title=title, type=TaskType.written, points=5)
        db.add(t)
    await db.flush()

    today = date(2026, 5, 18)  # Monday
    tasks = await generate_daily_tasks(db, child.id, today)
    assert len(tasks) == 2
    assert all(t.status == TaskStatus.pending for t in tasks)


@pytest.mark.asyncio
async def test_no_templates_empty_list(db: AsyncSession, seed_data):
    """No templates for today → empty task list."""
    child = seed_data["luobo"]
    today = date(2026, 5, 20)  # Wednesday, no templates
    tasks = await generate_daily_tasks(db, child.id, today)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_fallback_generation_on_get(db: AsyncSession, seed_data):
    """get_daily_tasks triggers generation if none exist."""
    child = seed_data["luobo"]
    t = TaskTemplate(child_id=child.id, weekday=1, title="fallback任务", type=TaskType.written, points=5)
    db.add(t)
    await db.flush()

    today = date(2026, 5, 18)  # Monday
    tasks = await get_daily_tasks(db, child.id, today)
    assert len(tasks) == 1
    assert tasks[0].title == "fallback任务"


@pytest.mark.asyncio
async def test_idempotent_generation(db: AsyncSession, seed_data):
    """Running generation twice does not create duplicates."""
    child = seed_data["luobo"]
    t = TaskTemplate(child_id=child.id, weekday=1, title="幂等测试", type=TaskType.written, points=5)
    db.add(t)
    await db.flush()

    today = date(2026, 5, 18)
    tasks1 = await generate_daily_tasks(db, child.id, today)
    tasks2 = await generate_daily_tasks(db, child.id, today)
    assert len(tasks1) == 1
    assert len(tasks2) == 1
    assert tasks1[0].id == tasks2[0].id


@pytest.mark.asyncio
async def test_new_template_generates_new_task(db: AsyncSession, seed_data):
    """Adding a new template after initial generation creates only the missing task."""
    child = seed_data["luobo"]
    t1 = TaskTemplate(child_id=child.id, weekday=1, title="已存在的任务", type=TaskType.written, points=5)
    db.add(t1)
    await db.flush()

    today = date(2026, 5, 18)
    tasks1 = await generate_daily_tasks(db, child.id, today)
    assert len(tasks1) == 1

    # Add a second template
    t2 = TaskTemplate(child_id=child.id, weekday=1, title="新增的任务", type=TaskType.reading, points=3)
    db.add(t2)
    await db.flush()

    tasks2 = await generate_daily_tasks(db, child.id, today)
    assert len(tasks2) == 2
    titles = {t.title for t in tasks2}
    assert "已存在的任务" in titles
    assert "新增的任务" in titles


@pytest.mark.asyncio
async def test_conditional_task_inserted_when_all_done(db: AsyncSession, seed_data):
    """Conditional tasks are inserted when all required tasks are completed."""
    child = seed_data["luobo"]
    # Create a template and a conditional task
    t = TaskTemplate(child_id=child.id, weekday=1, title="必做任务", type=TaskType.written, points=5)
    db.add(t)
    ct = ConditionalTask(child_id=child.id, title="条件任务", type=TaskType.reading, points=3)
    db.add(ct)
    await db.flush()

    today = date(2026, 5, 18)
    await generate_daily_tasks(db, child.id, today)

    # Mark the required task as done
    result = await db.execute(
        select(DailyTask).where(DailyTask.child_id == child.id, DailyTask.is_conditional == False)
    )
    task = result.scalars().first()
    task.status = TaskStatus.done
    task.completed_at = datetime.utcnow()
    await db.flush()

    await check_and_insert_conditional_tasks(db, child.id, today)

    result = await db.execute(
        select(DailyTask).where(DailyTask.child_id == child.id, DailyTask.is_conditional == True)
    )
    cond_tasks = list(result.scalars().all())
    assert len(cond_tasks) == 1
    assert cond_tasks[0].title == "条件任务"


@pytest.mark.asyncio
async def test_conditional_task_not_inserted_when_pending(db: AsyncSession, seed_data):
    """Conditional tasks are NOT inserted when some required tasks are still pending."""
    child = seed_data["luobo"]
    t1 = TaskTemplate(child_id=child.id, weekday=1, title="任务A", type=TaskType.written, points=5)
    t2 = TaskTemplate(child_id=child.id, weekday=1, title="任务B", type=TaskType.written, points=5)
    db.add_all([t1, t2])
    ct = ConditionalTask(child_id=child.id, title="条件任务", type=TaskType.reading, points=3)
    db.add(ct)
    await db.flush()

    today = date(2026, 5, 18)
    await generate_daily_tasks(db, child.id, today)

    # Only mark one task as done
    result = await db.execute(
        select(DailyTask).where(DailyTask.child_id == child.id, DailyTask.is_conditional == False)
    )
    task = result.scalars().first()
    task.status = TaskStatus.done
    task.completed_at = datetime.utcnow()
    await db.flush()

    await check_and_insert_conditional_tasks(db, child.id, today)

    result = await db.execute(
        select(DailyTask).where(DailyTask.child_id == child.id, DailyTask.is_conditional == True)
    )
    assert len(list(result.scalars().all())) == 0


@pytest.mark.asyncio
async def test_api_daily_tasks_fallback(client: AsyncClient, parent_token, seed_data):
    """API endpoint triggers fallback generation when no tasks exist."""
    child_id = seed_data["luobo"].id
    # First create a template for today (Monday)
    await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "API回退测试", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )

    resp = await client.get(
        f"/api/daily-tasks/{child_id}/2026-05-18",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1
