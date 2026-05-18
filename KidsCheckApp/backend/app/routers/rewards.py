from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import User
from app.schemas.schemas import (
    RewardCreate, RewardUpdate, RewardResponse, RewardRedemptionResponse,
)
from app.services import reward_service
from app.services.action_log_service import log_action

router = APIRouter(prefix="/api/rewards", tags=["rewards"])


@router.get("", response_model=list[RewardResponse])
async def list_rewards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rewards = await reward_service.list_rewards(db)
    return [RewardResponse(id=r.id, title=r.title, cost_points=r.cost_points,
                          description=r.description, image_url=r.image_url) for r in rewards]


@router.post("", response_model=RewardResponse)
async def create_reward(
    data: RewardCreate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    reward = await reward_service.create_reward(db, data)
    await log_action(db, user.id, "create_reward", "reward", reward.id)
    return RewardResponse(id=reward.id, title=reward.title, cost_points=reward.cost_points,
                          description=reward.description, image_url=reward.image_url)


@router.put("/{reward_id}", response_model=RewardResponse)
async def update_reward(
    reward_id: int,
    data: RewardUpdate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    reward = await reward_service.update_reward(db, reward_id, data)
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    await log_action(db, user.id, "update_reward", "reward", reward_id)
    return RewardResponse(id=reward.id, title=reward.title, cost_points=reward.cost_points,
                          description=reward.description, image_url=reward.image_url)


@router.delete("/{reward_id}")
async def delete_reward(
    reward_id: int,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    if not await reward_service.delete_reward(db, reward_id):
        raise HTTPException(status_code=404, detail="Reward not found")
    await log_action(db, user.id, "delete_reward", "reward", reward_id)
    return {"ok": True}


@router.post("/{reward_id}/redeem", response_model=RewardRedemptionResponse)
async def redeem_reward(
    reward_id: int,
    child_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        redemption = await reward_service.redeem_reward(db, child_id, reward_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_action(db, user.id, "redeem_reward", "reward", reward_id,
                     {"child_id": child_id, "points_spent": redemption.points_spent})
    return RewardRedemptionResponse(
        id=redemption.id, child_id=redemption.child_id, reward_id=redemption.reward_id,
        points_spent=redemption.points_spent, redeemed_at=redemption.redeemed_at,
        status=redemption.status.value,
    )


@router.put("/redemptions/{redemption_id}/fulfill")
async def fulfill_redemption(
    redemption_id: int,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    redemption = await reward_service.fulfill_redemption(db, redemption_id)
    if not redemption:
        raise HTTPException(status_code=404, detail="Redemption not found or already fulfilled")
    await log_action(db, user.id, "fulfill_redemption", "reward_redemption", redemption_id)
    return {"ok": True}
