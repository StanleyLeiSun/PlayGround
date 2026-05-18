from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ActionLog


async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    metadata: dict | None = None,
):
    entry = ActionLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata,
    )
    db.add(entry)
    await db.flush()
