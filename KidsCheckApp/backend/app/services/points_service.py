from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PointAccount, PointTransaction


async def award_points(db: AsyncSession, child_id: int, amount: int, task_id: int) -> PointAccount:
    """Award points to child for completing a task (idempotent)."""
    # Check for duplicate award
    existing = await db.execute(
        select(PointTransaction).where(
            PointTransaction.child_id == child_id,
            PointTransaction.related_task_id == task_id,
            PointTransaction.reason == "task_completed",
        )
    )
    if existing.scalars().first():
        # Already awarded
        result = await db.execute(select(PointAccount).where(PointAccount.child_id == child_id))
        return result.scalar_one()

    # Get account
    result = await db.execute(select(PointAccount).where(PointAccount.child_id == child_id))
    account = result.scalar_one_or_none()
    if not account:
        account = PointAccount(child_id=child_id, balance=0)
        db.add(account)
        await db.flush()

    account.balance += amount

    transaction = PointTransaction(
        child_id=child_id,
        amount=amount,
        reason="task_completed",
        related_task_id=task_id,
    )
    db.add(transaction)
    await db.flush()
    return account


async def get_balance(db: AsyncSession, child_id: int) -> tuple[int, list[PointTransaction]]:
    result = await db.execute(select(PointAccount).where(PointAccount.child_id == child_id))
    account = result.scalar_one_or_none()
    balance = account.balance if account else 0

    tx_result = await db.execute(
        select(PointTransaction)
        .where(PointTransaction.child_id == child_id)
        .order_by(PointTransaction.created_at.desc())
        .limit(50)
    )
    transactions = list(tx_result.scalars().all())
    return balance, transactions


async def deduct_points(db: AsyncSession, child_id: int, amount: int, reward_id: int) -> bool:
    """Deduct points for reward redemption. Returns False if insufficient."""
    result = await db.execute(select(PointAccount).where(PointAccount.child_id == child_id))
    account = result.scalar_one_or_none()
    if not account or account.balance < amount:
        return False

    account.balance -= amount
    transaction = PointTransaction(
        child_id=child_id,
        amount=-amount,
        reason="reward_redeemed",
        related_task_id=reward_id,
    )
    db.add(transaction)
    await db.flush()
    return True
