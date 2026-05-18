from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_parent
from app.models.models import User, ActionLog, UserRole
from app.schemas.schemas import ActionLogResponse

router = APIRouter(prefix="/api/action-logs", tags=["action-logs"])


@router.get("", response_model=list[ActionLogResponse])
async def get_action_logs(
    user_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    query = select(ActionLog).order_by(ActionLog.created_at.desc())

    if user_id:
        query = query.where(ActionLog.user_id == user_id)
    if start_date:
        query = query.where(ActionLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(ActionLog.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        ActionLogResponse(
            id=l.id, user_id=l.user_id, action=l.action,
            target_type=l.target_type, target_id=l.target_id,
            metadata=l.metadata, created_at=l.created_at,
        )
        for l in logs
    ]
