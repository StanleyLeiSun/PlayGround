import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import OralRecording, DailyTask, TaskTemplate, TaskType
from app.config import UPLOAD_DIR


RECORDINGS_DIR = UPLOAD_DIR.parent / "recordings"


async def save_recording(
    db: AsyncSession,
    daily_task_id: int,
    user_id: int,
    file_bytes: bytes,
    duration: float,
) -> OralRecording:
    """Save audio recording file and create DB record."""
    task_result = await db.execute(select(DailyTask).where(DailyTask.id == daily_task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise ValueError("Task not found")

    filename = f"{uuid.uuid4().hex}.m4a"
    task_date = task.date.date() if hasattr(task.date, 'date') else task.date
    rel_dir = RECORDINGS_DIR / str(task.child_id) / str(task_date)
    rel_dir.mkdir(parents=True, exist_ok=True)

    filepath = rel_dir / filename
    filepath.write_bytes(file_bytes)

    recording = OralRecording(
        daily_task_id=daily_task_id,
        audio_url=f"/recordings/{task.child_id}/{task_date}/{filename}",
        duration=duration,
        recorded_by=user_id,
        recorded_at=datetime.utcnow(),
    )
    db.add(recording)
    await db.flush()
    await db.refresh(recording)
    return recording


async def get_recordings(db: AsyncSession, task_id: int) -> list[OralRecording]:
    """Get all recordings for a task, ordered by recorded_at descending."""
    result = await db.execute(
        select(OralRecording)
        .where(OralRecording.daily_task_id == task_id)
        .order_by(OralRecording.recorded_at.desc())
    )
    return list(result.scalars().all())


async def save_oral_image(
    db: AsyncSession,
    template_id: int,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """Save oral practice image for a template and update the template's oral_image_url."""
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise ValueError("Template not found")
    if template.type != TaskType.oral:
        raise ValueError("Image upload only allowed for oral templates")

    ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    rel_dir = UPLOAD_DIR / "oral" / str(template_id)
    rel_dir.mkdir(parents=True, exist_ok=True)

    filepath = rel_dir / filename
    filepath.write_bytes(file_bytes)

    template.oral_image_url = f"/photos/oral/{template_id}/{filename}"
    await db.flush()
    await db.refresh(template)
    return template.oral_image_url
