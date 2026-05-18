import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CheckInPhoto, DailyTask
from app.config import UPLOAD_DIR


async def save_photo(
    db: AsyncSession,
    daily_task_id: int,
    user_id: int,
    file_bytes: bytes,
    content_type: str,
) -> CheckInPhoto:
    """Save photo file and create DB record."""
    ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"

    task_result = await db.execute(select(DailyTask).where(DailyTask.id == daily_task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise ValueError("Task not found")

    from datetime import date
    task_date = task.date.date() if hasattr(task.date, 'date') else task.date
    rel_dir = UPLOAD_DIR / str(task.child_id) / str(task_date)
    rel_dir.mkdir(parents=True, exist_ok=True)

    filepath = rel_dir / filename
    filepath.write_bytes(file_bytes)

    photo = CheckInPhoto(
        daily_task_id=daily_task_id,
        photo_url=f"/photos/{task.child_id}/{task_date}/{filename}",
        uploaded_by=user_id,
        uploaded_at=datetime.utcnow(),
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)
    return photo


async def get_photo(db: AsyncSession, photo_id: int) -> CheckInPhoto | None:
    result = await db.execute(select(CheckInPhoto).where(CheckInPhoto.id == photo_id))
    return result.scalar_one_or_none()


async def review_photo(db: AsyncSession, photo_id: int, reviewed: bool, note: str | None) -> CheckInPhoto | None:
    result = await db.execute(select(CheckInPhoto).where(CheckInPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        return None
    photo.reviewed = reviewed
    photo.review_note = note
    await db.flush()
    await db.refresh(photo)
    return photo
