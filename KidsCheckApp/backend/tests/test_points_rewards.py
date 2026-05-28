"""Tests for points and rewards: awarding, balance, redemption, RBAC."""
import pytest
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DailyTask, TaskTemplate, TaskType, TaskStatus, PointAccount,
    PointTransaction, Reward, RewardRedemption, RedemptionStatus,
)
from app.services.daily_task_service import generate_daily_tasks, check_in_task
from app.services.points_service import award_points, get_balance, deduct_points
from tests.conftest import auth_header


# --- Service-level tests ---

@pytest.mark.asyncio
async def test_points_awarded_on_checkin(db: AsyncSession, seed_data):
    child = seed_data["luobo"]
    parent = seed_data["users"]["baba"]
    t = TaskTemplate(child_id=child.id, weekday=1, title="积分测试", type=TaskType.reading, points=8)
    db.add(t)
    await db.flush()

    tasks = await generate_daily_tasks(db, child.id, date(2026, 5, 18))
    await check_in_task(db, tasks[0].id, parent.id, has_photo=False)

    balance, _ = await get_balance(db, child.id)
    assert balance == 8


@pytest.mark.asyncio
async def test_no_double_awarding(db: AsyncSession, seed_data):
    child = seed_data["luobo"]
    t = TaskTemplate(child_id=child.id, weekday=1, title="幂等积分", type=TaskType.reading, points=5)
    db.add(t)
    await db.flush()

    tasks = await generate_daily_tasks(db, child.id, date(2026, 5, 18))
    await award_points(db, child.id, 5, tasks[0].id)
    await award_points(db, child.id, 5, tasks[0].id)

    balance, _ = await get_balance(db, child.id)
    assert balance == 5


# --- API-level tests ---

@pytest.mark.asyncio
async def test_query_balance_and_transactions(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    parent = seed_data["users"]["baba"]

    t = TaskTemplate(child_id=child_id, weekday=1, title="余额查询", type=TaskType.reading, points=10)
    committed_db.add(t)
    await committed_db.flush()

    tasks = await generate_daily_tasks(committed_db, child_id, date(2026, 5, 18))
    await check_in_task(committed_db, tasks[0].id, parent.id, has_photo=False)
    await committed_db.commit()

    resp = await client.get(f"/api/points/{child_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 10
    assert len(data["transactions"]) >= 1


@pytest.mark.asyncio
async def test_create_reward(client: AsyncClient, parent_token, seed_data):
    resp = await client.post(
        "/api/rewards",
        json={"title": "看一集动画片", "cost_points": 10, "description": "30分钟"},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "看一集动画片"
    assert data["cost_points"] == 10


@pytest.mark.asyncio
async def test_delete_reward(client: AsyncClient, parent_token, seed_data):
    create_resp = await client.post(
        "/api/rewards",
        json={"title": "待删除", "cost_points": 5},
        headers=auth_header(parent_token),
    )
    reward_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/rewards/{reward_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_successful_redemption(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    await award_points(committed_db, child_id, 15, None)
    await committed_db.commit()

    reward_resp = await client.post(
        "/api/rewards",
        json={"title": "看动画片", "cost_points": 10},
        headers=auth_header(parent_token),
    )
    reward_id = reward_resp.json()["id"]

    resp = await client.post(
        f"/api/rewards/{reward_id}/redeem",
        data={"child_id": str(child_id)},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200

    # Check balance via service
    async with AsyncSession(bind=committed_db.bind) as check_db:
        balance, _ = await get_balance(check_db, child_id)
        assert balance == 5


@pytest.mark.asyncio
async def test_insufficient_points_redemption(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    await award_points(committed_db, child_id, 5, None)
    await committed_db.commit()

    reward_resp = await client.post(
        "/api/rewards",
        json={"title": "贵重奖励", "cost_points": 30},
        headers=auth_header(parent_token),
    )
    reward_id = reward_resp.json()["id"]

    resp = await client.post(
        f"/api/rewards/{reward_id}/redeem",
        data={"child_id": str(child_id)},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_fulfillment_by_parent(client: AsyncClient, parent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id
    await award_points(committed_db, child_id, 20, None)
    await committed_db.commit()

    reward_resp = await client.post(
        "/api/rewards",
        json={"title": "可兑现", "cost_points": 10},
        headers=auth_header(parent_token),
    )
    reward_id = reward_resp.json()["id"]

    await client.post(
        f"/api/rewards/{reward_id}/redeem",
        data={"child_id": str(child_id)},
        headers=auth_header(parent_token),
    )

    # Verify redemption is auto-fulfilled on creation
    async with AsyncSession(bind=committed_db.bind) as check_db:
        result = await check_db.execute(
            select(RewardRedemption).where(RewardRedemption.child_id == child_id)
        )
        redemption = result.scalars().first()
    assert redemption is not None
    assert redemption.status.value == "fulfilled"


@pytest.mark.asyncio
async def test_grandparent_cannot_fulfill(client: AsyncClient, grandparent_token, seed_data, committed_db):
    child_id = seed_data["luobo"].id

    reward = Reward(title="test", cost_points=10)
    committed_db.add(reward)
    await committed_db.flush()

    redemption = RewardRedemption(
        child_id=child_id, reward_id=reward.id,
        points_spent=10, status=RedemptionStatus.pending,
    )
    committed_db.add(redemption)
    await committed_db.flush()
    await committed_db.commit()

    resp = await client.put(
        f"/api/rewards/redemptions/{redemption.id}/fulfill",
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_grandparent_cannot_create_reward(client: AsyncClient, grandparent_token, seed_data):
    resp = await client.post(
        "/api/rewards",
        json={"title": "test", "cost_points": 10},
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403
