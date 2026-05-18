"""Tests for check-in flow: photo requirement, duplicate prevention, operator identity."""
import io
import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DailyTask, TaskTemplate, TaskType, TaskStatus, CheckInPhoto, PointAccount,
)
from app.services.daily_task_service import generate_daily_tasks
from tests.conftest import auth_header


async def _create_daily_task(db: AsyncSession, child_id: int, task_type: TaskType, title: str = "测试任务") -> DailyTask:
    t = TaskTemplate(child_id=child_id, weekday=1, title=title, type=task_type, points=5)
    db.add(t)
    await db.flush()
    tasks = await generate_daily_tasks(db, child_id, date(2026, 5, 18))
    return tasks[0]


# --- API-level tests (use committed_db so data is visible to API sessions) ---

@pytest.mark.asyncio
async def test_reading_task_checkin_without_photo(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    task = await _create_daily_task(committed_db, child_id, TaskType.reading)
    await committed_db.commit()

    resp = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["completed_by"] is not None


@pytest.mark.asyncio
async def test_reading_task_checkin_with_photo(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    task = await _create_daily_task(committed_db, child_id, TaskType.reading)
    await committed_db.commit()

    photo = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    resp = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        files={"photo": ("test.jpg", photo, "image/jpeg")},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_written_task_checkin_with_photo(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    task = await _create_daily_task(committed_db, child_id, TaskType.written)
    await committed_db.commit()

    photo = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    resp = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        files={"photo": ("test.jpg", photo, "image/jpeg")},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_written_task_checkin_without_photo_fails(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    task = await _create_daily_task(committed_db, child_id, TaskType.written)
    await committed_db.commit()

    resp = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_duplicate_checkin_returns_409(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    task = await _create_daily_task(committed_db, child_id, TaskType.reading)
    await committed_db.commit()

    resp1 = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        headers=auth_header(parent_token),
    )
    assert resp1.status_code == 200

    resp2 = await client.post(
        f"/api/daily-tasks/{task.id}/check-in",
        headers=auth_header(parent_token),
    )
    assert resp2.status_code in (409, 400)


# --- Service-level tests (use db directly, no API calls) ---

@pytest.mark.asyncio
async def test_checkin_records_operator_identity(db: AsyncSession, seed_data):
    child = seed_data["luobo"]
    parent = seed_data["users"]["baba"]
    task = await _create_daily_task(db, child.id, TaskType.reading)

    from app.services.daily_task_service import check_in_task
    result = await check_in_task(db, task.id, parent.id, has_photo=False)
    assert result.completed_by == parent.id
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_grandparent_checkin_records_identity(db: AsyncSession, seed_data):
    child = seed_data["luobo"]
    gp = seed_data["users"]["yeye"]
    task = await _create_daily_task(db, child.id, TaskType.reading)

    from app.services.daily_task_service import check_in_task
    result = await check_in_task(db, task.id, gp.id, has_photo=False)
    assert result.completed_by == gp.id


@pytest.mark.asyncio
async def test_checkin_awards_points(db: AsyncSession, seed_data):
    child = seed_data["luobo"]
    parent = seed_data["users"]["baba"]
    task = await _create_daily_task(db, child.id, TaskType.reading)

    from app.services.daily_task_service import check_in_task
    await check_in_task(db, task.id, parent.id, has_photo=False)

    result = await db.execute(select(PointAccount).where(PointAccount.child_id == child.id))
    account = result.scalar_one()
    assert account.balance == 5


@pytest.mark.asyncio
async def test_checkin_nonexistent_task(db: AsyncSession, seed_data):
    from app.services.daily_task_service import check_in_task
    with pytest.raises(ValueError, match="Task not found"):
        await check_in_task(db, 99999, 1, has_photo=False)
