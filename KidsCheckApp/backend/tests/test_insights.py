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
    assert "completions_by_type" in data
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
    assert data["completions_by_type"] == {}
    assert data["streak"] == 0


@pytest.mark.asyncio
async def test_insights_completion_rate_calculation(client, parent_token, seed_data, seed_tasks):
    """Test that completion rate is calculated correctly."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    # We created 7 tasks, 5 completed
    assert data["total_tasks"] == 7
    assert data["completed_tasks"] == 5
    expected_rate = round(5 / 7 * 100, 1)
    assert data["completion_rate"] == expected_rate


@pytest.mark.asyncio
async def test_insights_completions_by_type(client, parent_token, seed_data, seed_tasks):
    """Test that completions_by_type is populated correctly."""
    luobo = seed_data["luobo"]
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    # We have reading and written tasks, 5 completed total
    completions = data["completions_by_type"]
    assert "reading" in completions or "written" in completions


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
    resp = await client.get(
        f"/api/insights/{luobo.id}",
        params={"period": "week"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    # 5 completed tasks * 10 points each
    assert data["total_points_earned"] == 50
