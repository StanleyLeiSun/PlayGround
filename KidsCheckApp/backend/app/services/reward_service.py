from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Reward, RewardRedemption, RedemptionStatus
from app.schemas.schemas import RewardCreate, RewardUpdate
from app.services import points_service


async def list_rewards(db: AsyncSession) -> list[Reward]:
    result = await db.execute(select(Reward).order_by(Reward.cost_points))
    return list(result.scalars().all())


async def create_reward(db: AsyncSession, data: RewardCreate) -> Reward:
    reward = Reward(
        title=data.title,
        cost_points=data.cost_points,
        description=data.description,
        image_url=data.image_url,
    )
    db.add(reward)
    await db.flush()
    await db.refresh(reward)
    return reward


async def update_reward(db: AsyncSession, reward_id: int, data: RewardUpdate) -> Reward | None:
    result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reward, field, value)
    await db.flush()
    await db.refresh(reward)
    return reward


async def delete_reward(db: AsyncSession, reward_id: int) -> bool:
    result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        return False
    await db.delete(reward)
    await db.flush()
    return True


async def redeem_reward(db: AsyncSession, child_id: int, reward_id: int) -> RewardRedemption:
    result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        raise ValueError("Reward not found")

    success = await points_service.deduct_points(db, child_id, reward.cost_points, reward_id)
    if not success:
        raise ValueError("Insufficient points")

    redemption = RewardRedemption(
        child_id=child_id,
        reward_id=reward_id,
        points_spent=reward.cost_points,
        redeemed_at=datetime.utcnow(),
        status=RedemptionStatus.pending,
    )
    db.add(redemption)
    await db.flush()
    await db.refresh(redemption)
    return redemption


async def fulfill_redemption(db: AsyncSession, redemption_id: int) -> RewardRedemption | None:
    result = await db.execute(
        select(RewardRedemption).where(RewardRedemption.id == redemption_id)
    )
    redemption = result.scalar_one_or_none()
    if not redemption or redemption.status == RedemptionStatus.fulfilled:
        return None
    redemption.status = RedemptionStatus.fulfilled
    await db.flush()
    await db.refresh(redemption)
    return redemption
