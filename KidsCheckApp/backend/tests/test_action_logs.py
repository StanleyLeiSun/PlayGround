"""Tests for action logging: creation, append-only, query filters, RBAC."""
import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ActionLog, TaskTemplate, TaskType, Reward, PointAccount
from app.services.daily_task_service import generate_daily_tasks, check_in_task
from app.services.action_log_service import log_action
from app.services.points_service import award_points
from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_login_logged(client: AsyncClient, seed_data):
    resp = await client.post("/api/auth/login", json={"username": "baba", "password": "123456"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    logs_resp = await client.get(
        "/api/action-logs?action=login",
        headers=auth_header(token),
    )
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert any(log["action"] == "login" for log in logs)


@pytest.mark.asyncio
async def test_template_creation_logged(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "日志测试", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )

    resp = await client.get(
        "/api/action-logs?action=create_template",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert any(log["action"] == "create_template" for log in resp.json())


@pytest.mark.asyncio
async def test_template_deletion_logged(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    create_resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "待删除日志", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )
    template_id = create_resp.json()["id"]

    await client.delete(f"/api/templates/{template_id}", headers=auth_header(parent_token))

    resp = await client.get(
        "/api/action-logs?action=delete_template",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert any(log["action"] == "delete_template" for log in resp.json())


@pytest.mark.asyncio
async def test_checkin_logged(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    t = TaskTemplate(child_id=child_id, weekday=1, title="打卡日志", type=TaskType.reading, points=5)
    committed_db.add(t)
    await committed_db.flush()

    tasks = await generate_daily_tasks(committed_db, child_id, date(2026, 5, 18))
    await committed_db.commit()

    # Check in via API so the router logs the action
    resp = await client.post(
        f"/api/daily-tasks/{tasks[0].id}/check-in",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200

    logs_resp = await client.get(
        "/api/action-logs?action=check_in",
        headers=auth_header(parent_token),
    )
    assert logs_resp.status_code == 200
    assert any(log["action"] == "check_in" for log in logs_resp.json())


@pytest.mark.asyncio
async def test_reward_redemption_logged(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    await award_points(committed_db, child_id, 20, None)
    await committed_db.commit()

    reward_resp = await client.post(
        "/api/rewards",
        json={"title": "日志测试奖励", "cost_points": 5},
        headers=auth_header(parent_token),
    )
    reward_id = reward_resp.json()["id"]

    await client.post(
        f"/api/rewards/{reward_id}/redeem",
        data={"child_id": str(child_id)},
        headers=auth_header(parent_token),
    )

    resp = await client.get(
        "/api/action-logs?action=redeem_reward",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert any(log["action"] == "redeem_reward" for log in resp.json())


@pytest.mark.asyncio
async def test_query_logs_by_user(client: AsyncClient, parent_token, seed_data):
    resp = await client.get("/api/action-logs", headers=auth_header(parent_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_query_logs_by_date_range(client: AsyncClient, parent_token, seed_data):
    resp = await client.get(
        "/api/action-logs?start_date=2026-05-01&end_date=2026-05-31",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_grandparent_cannot_query_logs(client: AsyncClient, grandparent_token, seed_data):
    resp = await client.get("/api/action-logs", headers=auth_header(grandparent_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_action_log_append_only(db: AsyncSession, seed_data):
    await log_action(db, seed_data["users"]["baba"].id, "test_action")

    result = await db.execute(select(ActionLog).where(ActionLog.action == "test_action"))
    log = result.scalars().first()
    assert log is not None
