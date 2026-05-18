"""Tests for progress tracking: query, role-based date restriction, photo review."""
import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DailyTask, TaskTemplate, TaskType, TaskStatus, CheckInPhoto,
)
from app.services.daily_task_service import generate_daily_tasks, check_in_task
from tests.conftest import auth_header


async def _setup_tasks(db: AsyncSession, child_id: int, parent_id: int):
    t1 = TaskTemplate(child_id=child_id, weekday=1, title="已完成", type=TaskType.reading, points=5)
    t2 = TaskTemplate(child_id=child_id, weekday=1, title="未完成", type=TaskType.reading, points=3)
    db.add_all([t1, t2])
    await db.flush()

    tasks = await generate_daily_tasks(db, child_id, date(2026, 5, 18))
    await check_in_task(db, tasks[0].id, parent_id, has_photo=False)
    return tasks


@pytest.mark.asyncio
async def test_query_progress_today(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id
    await _setup_tasks(committed_db, child_id, parent_id)
    await committed_db.commit()

    resp = await client.get(
        f"/api/progress/{child_id}/2026-05-18",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 2
    assert data["completed_tasks"] == 1
    assert data["today_points"] == 5
    assert len(data["tasks"]) == 2


@pytest.mark.asyncio
async def test_parent_can_query_past_date(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id
    await _setup_tasks(committed_db, child_id, parent_id)
    await committed_db.commit()

    resp = await client.get(
        f"/api/progress/{child_id}/2026-05-18",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_grandparent_cannot_query_past_date(client: AsyncClient, grandparent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id
    await _setup_tasks(committed_db, child_id, parent_id)
    await committed_db.commit()

    resp = await client.get(
        f"/api/progress/{child_id}/2026-05-17",
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_timeline_order(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id
    await _setup_tasks(committed_db, child_id, parent_id)
    await committed_db.commit()

    resp = await client.get(
        f"/api/progress/{child_id}/2026-05-18",
        headers=auth_header(parent_token),
    )
    tasks = resp.json()["tasks"]
    completed = [t for t in tasks if t["status"] == "done"]
    pending = [t for t in tasks if t["status"] == "pending"]
    assert len(completed) >= 1
    assert len(pending) >= 1
    done_indices = [i for i, t in enumerate(tasks) if t["status"] == "done"]
    pending_indices = [i for i, t in enumerate(tasks) if t["status"] == "pending"]
    assert max(done_indices) < min(pending_indices)


@pytest.mark.asyncio
async def test_cumulative_points(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id
    await _setup_tasks(committed_db, child_id, parent_id)
    await committed_db.commit()

    resp = await client.get(
        f"/api/progress/{child_id}/2026-05-18",
        headers=auth_header(parent_token),
    )
    data = resp.json()
    assert data["cumulative_points"] == 5


@pytest.mark.asyncio
async def test_photo_review(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent_id = seed_data["users"]["baba"].id

    t = TaskTemplate(child_id=child_id, weekday=1, title="拍照任务", type=TaskType.written, points=5)
    committed_db.add(t)
    await committed_db.flush()

    tasks = await generate_daily_tasks(committed_db, child_id, date(2026, 5, 18))
    task = tasks[0]

    photo = CheckInPhoto(
        daily_task_id=task.id,
        photo_url="/test/photo.jpg",
        uploaded_by=parent_id,
        uploaded_at=datetime.utcnow(),
    )
    committed_db.add(photo)
    task.status = TaskStatus.done
    task.completed_at = datetime.utcnow()
    task.completed_by = parent_id
    await committed_db.flush()
    await committed_db.refresh(photo)
    await committed_db.commit()

    resp = await client.put(
        f"/api/progress/{child_id}/photo/{photo.id}/review",
        json={"reviewed": True, "review_note": "很好"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
