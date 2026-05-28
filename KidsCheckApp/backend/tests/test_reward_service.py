"""Tests for reward_service functions."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Reward, RewardRedemption, RedemptionStatus
from app.schemas.schemas import RewardCreate, RewardUpdate
from app.services import reward_service, points_service


@pytest.mark.asyncio
async def test_list_rewards_empty(db: AsyncSession):
    """Test listing rewards when none exist."""
    rewards = await reward_service.list_rewards(db)
    assert rewards == []


@pytest.mark.asyncio
async def test_create_reward(db: AsyncSession):
    """Test creating a reward."""
    data = RewardCreate(
        title="Test Reward",
        cost_points=10,
        description="A test reward",
        image_url=None,
    )
    reward = await reward_service.create_reward(db, data)
    assert reward.id is not None
    assert reward.title == "Test Reward"
    assert reward.cost_points == 10
    assert reward.description == "A test reward"


@pytest.mark.asyncio
async def test_list_rewards_after_create(db: AsyncSession):
    """Test listing rewards after creating some."""
    data1 = RewardCreate(title="Reward 1", cost_points=10, description=None, image_url=None)
    data2 = RewardCreate(title="Reward 2", cost_points=20, description=None, image_url=None)
    await reward_service.create_reward(db, data1)
    await reward_service.create_reward(db, data2)

    rewards = await reward_service.list_rewards(db)
    assert len(rewards) == 2
    # Should be ordered by cost_points
    assert rewards[0].cost_points <= rewards[1].cost_points


@pytest.mark.asyncio
async def test_update_reward(db: AsyncSession):
    """Test updating a reward."""
    data = RewardCreate(title="Old Title", cost_points=10, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)

    update_data = RewardUpdate(title="New Title", cost_points=15)
    updated = await reward_service.update_reward(db, reward.id, update_data)
    assert updated is not None
    assert updated.title == "New Title"
    assert updated.cost_points == 15


@pytest.mark.asyncio
async def test_update_reward_not_found(db: AsyncSession):
    """Test updating a non-existent reward."""
    update_data = RewardUpdate(title="New Title")
    result = await reward_service.update_reward(db, 999, update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_reward(db: AsyncSession):
    """Test deleting a reward."""
    data = RewardCreate(title="To Delete", cost_points=10, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)

    result = await reward_service.delete_reward(db, reward.id)
    assert result is True

    rewards = await reward_service.list_rewards(db)
    assert len(rewards) == 0


@pytest.mark.asyncio
async def test_delete_reward_not_found(db: AsyncSession):
    """Test deleting a non-existent reward."""
    result = await reward_service.delete_reward(db, 999)
    assert result is False


@pytest.mark.asyncio
async def test_redeem_reward_success(db: AsyncSession, seed_data):
    """Test successful reward redemption."""
    child = seed_data["luobo"]

    # Award points first
    await points_service.award_points(db, child.id, 100, None)
    await db.commit()

    # Create reward
    data = RewardCreate(title="Redeemable", cost_points=50, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)
    await db.commit()

    # Redeem
    redemption = await reward_service.redeem_reward(db, child.id, reward.id)
    assert redemption.id is not None
    assert redemption.child_id == child.id
    assert redemption.reward_id == reward.id
    assert redemption.points_spent == 50
    assert redemption.status == RedemptionStatus.fulfilled


@pytest.mark.asyncio
async def test_redeem_reward_insufficient_points(db: AsyncSession, seed_data):
    """Test redemption with insufficient points."""
    child = seed_data["luobo"]

    # Create reward
    data = RewardCreate(title="Expensive", cost_points=100, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)
    await db.commit()

    # Try to redeem without enough points
    with pytest.raises(ValueError, match="Insufficient points"):
        await reward_service.redeem_reward(db, child.id, reward.id)


@pytest.mark.asyncio
async def test_redeem_reward_not_found(db: AsyncSession, seed_data):
    """Test redemption of non-existent reward."""
    child = seed_data["luobo"]

    with pytest.raises(ValueError, match="Reward not found"):
        await reward_service.redeem_reward(db, child.id, 999)


@pytest.mark.asyncio
async def test_fulfill_redemption(db: AsyncSession, seed_data):
    """Test that redemption is auto-fulfilled on creation."""
    child = seed_data["luobo"]

    # Award points and create reward
    await points_service.award_points(db, child.id, 100, None)
    data = RewardCreate(title="To Fulfill", cost_points=30, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)
    await db.commit()

    # Redeem — now auto-fulfilled
    redemption = await reward_service.redeem_reward(db, child.id, reward.id)
    await db.commit()
    assert redemption.status == RedemptionStatus.fulfilled


@pytest.mark.asyncio
async def test_fulfill_redemption_not_found(db: AsyncSession):
    """Test fulfilling a non-existent redemption."""
    result = await reward_service.fulfill_redemption(db, 999)
    assert result is None


@pytest.mark.asyncio
async def test_fulfill_redemption_already_fulfilled(db: AsyncSession, seed_data):
    """Test fulfilling an already fulfilled redemption."""
    child = seed_data["luobo"]

    # Award points and create reward
    await points_service.award_points(db, child.id, 100, None)
    data = RewardCreate(title="Already Done", cost_points=30, description=None, image_url=None)
    reward = await reward_service.create_reward(db, data)
    await db.commit()

    # Redeem and fulfill
    redemption = await reward_service.redeem_reward(db, child.id, reward.id)
    await db.commit()
    await reward_service.fulfill_redemption(db, redemption.id)
    await db.commit()

    # Try to fulfill again
    result = await reward_service.fulfill_redemption(db, redemption.id)
    assert result is None
