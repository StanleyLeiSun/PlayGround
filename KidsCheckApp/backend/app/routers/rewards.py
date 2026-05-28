import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import UPLOAD_DIR
from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import User, Reward, RewardRedemption, Child
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


ALLOWED_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@router.post("/{reward_id}/redeem", response_model=RewardRedemptionResponse)
async def redeem_reward(
    reward_id: int,
    child_id_q: int | None = Query(None, alias="child_id"),
    child_id: int = Form(None),
    photo: UploadFile = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    effective_child_id = child_id_q if child_id_q is not None else child_id
    if effective_child_id is None:
        raise HTTPException(status_code=400, detail="child_id is required")

    photo_url = None
    if photo:
        if photo.content_type and photo.content_type not in ALLOWED_PHOTO_MIME:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {photo.content_type}")
        file_bytes = await photo.read()
        if len(file_bytes) > 2_097_152:
            raise HTTPException(status_code=400, detail="Photo too large (max 2MB)")
        photo_dir = UPLOAD_DIR / "rewards" / str(effective_child_id)
        photo_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = photo_dir / filename
        filepath.write_bytes(file_bytes)
        photo_url = f"/photos/rewards/{effective_child_id}/{filename}"

    try:
        redemption = await reward_service.redeem_reward(db, effective_child_id, reward_id, photo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    reward_result = await db.execute(select(Reward).where(Reward.id == reward_id))
    reward = reward_result.scalar_one_or_none()
    child_result = await db.execute(select(Child).where(Child.id == effective_child_id))
    child = child_result.scalar_one_or_none()

    await log_action(db, user.id, "redeem_reward", "reward", reward_id,
                     {"child_id": effective_child_id, "points_spent": redemption.points_spent})
    return RewardRedemptionResponse(
        id=redemption.id, child_id=redemption.child_id,
        child_name=child.nickname if child else None,
        reward_id=redemption.reward_id,
        reward_title=reward.title if reward else None,
        points_spent=redemption.points_spent, redeemed_at=redemption.redeemed_at,
        status=redemption.status.value,
        photo_url=redemption.photo_url,
    )


@router.get("/redemptions", response_model=list[RewardRedemptionResponse])
async def list_redemptions(
    child_id: int = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(RewardRedemption).order_by(RewardRedemption.redeemed_at.desc())
    if child_id:
        query = query.where(RewardRedemption.child_id == child_id)
    result = await db.execute(query)
    redemptions = result.scalars().all()

    reward_ids = {r.reward_id for r in redemptions}
    child_ids = {r.child_id for r in redemptions}

    rewards_map = {}
    if reward_ids:
        rr = await db.execute(select(Reward).where(Reward.id.in_(reward_ids)))
        rewards_map = {r.id: r.title for r in rr.scalars().all()}

    children_map = {}
    if child_ids:
        cr = await db.execute(select(Child).where(Child.id.in_(child_ids)))
        children_map = {c.id: c.nickname for c in cr.scalars().all()}

    return [
        RewardRedemptionResponse(
            id=r.id, child_id=r.child_id,
            child_name=children_map.get(r.child_id),
            reward_id=r.reward_id,
            reward_title=rewards_map.get(r.reward_id),
            points_spent=r.points_spent,
            redeemed_at=r.redeemed_at,
            status=r.status.value,
            photo_url=r.photo_url,
        )
        for r in redemptions
    ]


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
