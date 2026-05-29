"""Tests for the insights router."""
import pytest
from datetime import date, datetime, timedelta

from app.models.models import (
    User, UserRole, Child, TaskTemplate, TaskType, TaskStatus,
    DailyTask, PointAccount, ConditionalTask,
)
from app.middleware.auth import create_token
from tests.conftest import auth_header


@pytest.fixture
async def seed_tasks(committed_db, seed_data):
    """Create some daily tasks for testing insights."""
    luobo = seed_data["luobo"]
    today = date.today()

    # Create tasks for the past 7 days
    tasks = []
    for i in range(7):
        task_date = datetime.combine(today - timedelta(days=i), datetime.min.time())
        task = DailyTask(
            child_id=luobo.id,
            title=f"Task {i}",
            type=TaskType.reading if i % 2 == 0 else TaskType.written,
            status=TaskStatus.done if i < 5 else TaskStatus.pending,
            points=10,
            date=task_date,
            source_template_id=None,
        )
        committed_db.add(task)
        tasks.append(task)

    await committed_db.commit()
    return tasks


@pytest.mark.asyncio
async def test_insights_week_period(client, parent_token, seed_data, seed_tasks):
    """Test insights with week period."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["child_id"] == luobo.id
    assert data["period"] == "week"
    assert data["total_tasks"] > 0
    assert data["completed_tasks"] > 0
    assert "completion_rate" in data
    assert "daily_stats" in data
    assert "task_stats" in data
    assert "streak" in data


@pytest.mark.asyncio
async def test_insights_month_period(client, parent_token, seed_data, seed_tasks):
    """Test insights with month period."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "month"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["child_id"] == luobo.id
    assert data["period"] == "month"


@pytest.mark.asyncio
async def test_insights_last_week_period(client, parent_token, seed_data, committed_db):
    """Test insights with last_week period returns full Mon-Sun range."""
    luobo = seed_data["luobo"]
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)

    # Create tasks for last week (Mon, Wed, Fri)
    for i in range(3):
        task_date = datetime.combine(last_monday + timedelta(days=i * 2), datetime.min.time())
        task = DailyTask(
            child_id=luobo.id,
            title=f"Last week task {i}",
            type=TaskType.reading,
            status=TaskStatus.done,
            points=10,
            date=task_date,
            source_template_id=None,
        )
        committed_db.add(task)
    await committed_db.commit()

    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "last_week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "last_week"
    assert data["total_tasks"] == 3
    assert data["completed_tasks"] == 3
    # Verify daily stats are within last week range
    for stat in data["daily_stats"]:
        stat_date = date.fromisoformat(stat["date"])
        assert stat_date >= last_monday
        assert stat_date <= last_monday + timedelta(days=6)


@pytest.mark.asyncio
async def test_insights_invalid_period(client, parent_token, seed_data):
    """Test insights with invalid period returns 422."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "year"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_insights_no_tasks(client, parent_token, seed_data):
    """Test insights with no tasks returns zero stats."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    assert data["completion_rate"] == 0.0
    assert data["daily_stats"] == []
    assert data["task_stats"] == []
    assert data["streak"] == 0


@pytest.mark.asyncio
async def test_insights_completion_rate_calculation(client, parent_token, seed_data, seed_tasks):
    """Test that completion rate is calculated correctly for this week."""
    luobo = seed_data["luobo"]
    today = date.today()
    # seed_tasks creates 7 tasks for today-0..today-6, first 5 completed.
    # This week (Mon..today) includes weekday()+1 tasks.
    days_in_week = today.weekday() + 1
    completed_in_week = min(5, days_in_week)  # first 5 are completed

    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == days_in_week
    assert data["completed_tasks"] == completed_in_week
    expected_rate = round(completed_in_week / days_in_week * 100, 1)
    assert data["completion_rate"] == expected_rate


@pytest.mark.asyncio
async def test_insights_task_stats(client, parent_token, seed_data, seed_tasks):
    """Test that task_stats is populated correctly with per-task breakdown."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    task_stats = data["task_stats"]
    assert len(task_stats) > 0
    for stat in task_stats:
        assert "title" in stat
        assert "completed" in stat
        assert "total" in stat
        assert "ratio" in stat
        assert 0 <= stat["ratio"] <= 1
        assert stat["completed"] <= stat["total"]


@pytest.mark.asyncio
async def test_insights_streak_calculation(client, parent_token, seed_data, committed_db):
    """Test streak calculation when all tasks are done for consecutive days."""
    luobo = seed_data["luobo"]
    today = date.today()

    # Create tasks for today and yesterday, all completed
    for i in range(2):
        task_date = datetime.combine(today - timedelta(days=i), datetime.min.time())
        task = DailyTask(
            child_id=luobo.id,
            title=f"Streak task {i}",
            type=TaskType.reading,
            status=TaskStatus.done,
            points=10,
            date=task_date,
            source_template_id=None,
        )
        committed_db.add(task)
    await committed_db.commit()

    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["streak"] == 2


@pytest.mark.asyncio
async def test_insights_grandparent_forbidden(client, grandparent_token, seed_data):
    """Test that grandparent cannot access insights."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_insights_daily_stats_order(client, parent_token, seed_data, seed_tasks):
    """Test that daily_stats are ordered by date ascending."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    daily_stats = data["daily_stats"]
    if len(daily_stats) > 1:
        dates = [s["date"] for s in daily_stats]
        assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_insights_daily_stats_fields(client, parent_token, seed_data, seed_tasks):
    """Test that each daily stat item has correct fields."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    for stat in data["daily_stats"]:
        assert "date" in stat
        assert "total" in stat
        assert "completed" in stat
        assert "points" in stat


@pytest.mark.asyncio
async def test_insights_points_earned(client, parent_token, seed_data, seed_tasks):
    """Test that total_points_earned is calculated correctly."""
    luobo = seed_data["luobo"]
    today = date.today()
    days_in_week = today.weekday() + 1
    completed_in_week = min(5, days_in_week)

    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_points_earned"] == completed_in_week * 10
