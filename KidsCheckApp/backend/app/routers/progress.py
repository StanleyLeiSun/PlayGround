from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import (
    User, DailyTask, TaskStatus, CheckInPhoto, PointAccount, PointTransaction, UserRole,
)
from app.schemas.schemas import ProgressResponse, DailyTaskResponse, CheckInPhotoResponse, PhotoReviewRequest
from app.services import daily_task_service, photo_service
from app.services.action_log_service import log_action

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{child_id}/{target_date}", response_model=ProgressResponse)
async def get_progress(
    child_id: int,
    target_date: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Grandparents can only view today
    if user.role == UserRole.grandparent and target_date != date.today():
        raise HTTPException(status_code=403, detail="Grandparents can only view today's progress")

    tasks = await daily_task_service.get_daily_tasks(db, child_id, target_date)

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.done)
    today_points = sum(t.points for t in tasks if t.status == TaskStatus.done)

    # Cumulative points
    result = await db.execute(select(PointAccount).where(PointAccount.child_id == child_id))
    account = result.scalar_one_or_none()
    cumulative = account.balance if account else 0

    completed_ids = {t.completed_by for t in tasks if t.completed_by}
    username_by_id: dict[int, str] = {}
    if completed_ids:
        result = await db.execute(select(User.id, User.username).where(User.id.in_(completed_ids)))
        username_by_id = {uid: name for uid, name in result.all()}

    task_responses = []
    for t in sorted(tasks, key=lambda x: (x.is_conditional, x.completed_at or datetime.max)):
        task_responses.append(DailyTaskResponse(
            id=t.id, child_id=t.child_id, date=t.date,
            title=t.title, type=t.type.value, points=t.points,
            status=t.status.value, completed_at=t.completed_at,
            completed_by=t.completed_by,
            completed_by_username=username_by_id.get(t.completed_by) if t.completed_by else None,
            is_conditional=t.is_conditional,
            photos=[
                CheckInPhotoResponse(
                    id=p.id, photo_url=p.photo_url, uploaded_by=p.uploaded_by,
                    uploaded_at=p.uploaded_at, reviewed=p.reviewed, review_note=p.review_note,
                )
                for p in (t.photos or [])
            ],
        ))

    return ProgressResponse(
        child_id=child_id,
        date=datetime.combine(target_date, datetime.min.time()),
        total_tasks=total,
        completed_tasks=completed,
        today_points=today_points,
        cumulative_points=cumulative,
        tasks=task_responses,
    )


@router.get("/{child_id}/photo/{photo_id}")
async def get_photo(
    child_id: int,
    photo_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    photo = await photo_service.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    # Return photo URL for client to fetch via static serving
    return {"photo_url": photo.photo_url}


@router.put("/{child_id}/photo/{photo_id}/review")
async def review_photo(
    child_id: int,
    photo_id: int,
    req: PhotoReviewRequest,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    photo = await photo_service.review_photo(db, photo_id, req.reviewed, req.review_note)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    await log_action(db, user.id, "review_photo", "check_in_photo", photo_id,
                     {"result": "valid" if req.reviewed else "needs-redo"})
    return {"ok": True}
