from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User, DailyTask, TaskType, TaskStatus
from app.schemas.schemas import DailyTaskResponse, CheckInPhotoResponse, OralRecordingResponse, AdhocTaskCreate
from app.services import daily_task_service, photo_service, oral_service
from app.services.action_log_service import log_action

router = APIRouter(prefix="/api/daily-tasks", tags=["daily-tasks"])


def _task_to_response(task, completed_by_username: str | None = None) -> DailyTaskResponse:
    return DailyTaskResponse(
        id=task.id,
        child_id=task.child_id,
        date=task.date,
        title=task.title,
        type=task.type.value,
        points=task.points,
        status=task.status.value,
        completed_at=task.completed_at,
        completed_by=task.completed_by,
        completed_by_username=completed_by_username,
        is_conditional=task.is_conditional,
        is_adhoc=task.is_adhoc,
        description=task.description,
        oral_image_url=task.oral_image_url,
        photos=[
            CheckInPhotoResponse(
                id=p.id, photo_url=p.photo_url, uploaded_by=p.uploaded_by,
                uploaded_at=p.uploaded_at, reviewed=p.reviewed, review_note=p.review_note,
            )
            for p in (task.photos or [])
        ],
        recordings=[
            OralRecordingResponse(
                id=r.id, audio_url=r.audio_url, duration=r.duration,
                recorded_by=r.recorded_by, recorded_at=r.recorded_at,
            )
            for r in (task.recordings or [])
        ],
    )


@router.get("/{task_id}/recordings", response_model=list[OralRecordingResponse])
async def get_recordings(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all recordings for an oral task."""
    recordings = await oral_service.get_recordings(db, task_id)
    return [
        OralRecordingResponse(
            id=r.id, audio_url=r.audio_url, duration=r.duration,
            recorded_by=r.recorded_by, recorded_at=r.recorded_at,
        )
        for r in recordings
    ]


@router.get("/{child_id}/{target_date}", response_model=list[DailyTaskResponse])
async def get_daily_tasks(
    child_id: int,
    target_date: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await daily_task_service.get_daily_tasks(db, child_id, target_date)
    completed_ids = {t.completed_by for t in tasks if t.completed_by}
    username_by_id: dict[int, str] = {}
    if completed_ids:
        result = await db.execute(select(User.id, User.username).where(User.id.in_(completed_ids)))
        username_by_id = {uid: name for uid, name in result.all()}
    return [_task_to_response(t, username_by_id.get(t.completed_by or -1)) for t in tasks]


@router.post("/{task_id}/check-in")
async def check_in(
    task_id: int,
    photo: UploadFile = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    has_photo = False
    if photo:
        file_bytes = await photo.read()
        if len(file_bytes) > 1_048_576:  # 1MB
            raise HTTPException(status_code=400, detail="Photo too large (max 1MB)")
        try:
            await photo_service.save_photo(db, task_id, user.id, file_bytes, photo.content_type or "image/jpeg")
            has_photo = True
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    try:
        task = await daily_task_service.check_in_task(db, task_id, user.id, has_photo)
    except ValueError as e:
        msg = str(e)
        if msg == "Already completed":
            raise HTTPException(status_code=409, detail=msg)
        if msg == "Task not found":
            raise HTTPException(status_code=404, detail=msg)
        if "Photo required" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    await log_action(db, user.id, "check_in", "daily_task", task_id,
                     {"child_id": task.child_id, "photo_uploaded": has_photo})

    return _task_to_response(task, user.username if task.completed_by == user.id else None)


@router.post("/{task_id}/undo")
async def undo_check_in(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await daily_task_service.undo_task(db, task_id)
    except ValueError as e:
        msg = str(e)
        if msg == "Task not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    await log_action(db, user.id, "undo_check_in", "daily_task", task_id,
                     {"child_id": task.child_id})
    return _task_to_response(task)


@router.post("/{task_id}/recording")
async def upload_recording(
    task_id: int,
    audio: UploadFile = File(...),
    duration: float = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a recording for an oral task. Marks the task as completed."""
    result = await db.execute(select(DailyTask).where(DailyTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.type != TaskType.oral:
        raise HTTPException(status_code=400, detail="Recording upload only allowed for oral tasks")
    if task.status == TaskStatus.done:
        raise HTTPException(status_code=400, detail="Already completed")
    if duration < 20:
        raise HTTPException(status_code=400, detail="Recording too short (minimum 20 seconds)")

    file_bytes = await audio.read()
    content_type = audio.content_type or ""
    if "mp4" not in content_type and "aac" not in content_type and "m4a" not in content_type:
        raise HTTPException(status_code=400, detail="Audio format must be AAC/M4A")

    try:
        recording = await oral_service.save_recording(db, task_id, user.id, file_bytes, duration)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    task = await daily_task_service.check_in_task(db, task_id, user.id, has_photo=False)

    await log_action(db, user.id, "oral_recording", "daily_task", task_id,
                     {"child_id": task.child_id, "duration": duration})

    return {
        "recording": OralRecordingResponse(
            id=recording.id, audio_url=recording.audio_url, duration=recording.duration,
            recorded_by=recording.recorded_by, recorded_at=recording.recorded_at,
        ),
        "task": _task_to_response(task, user.username),
    }


@router.post("/{child_id}/adhoc", response_model=DailyTaskResponse)
async def create_adhoc_task(
    child_id: int,
    data: AdhocTaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = DailyTask(
        child_id=child_id,
        date=datetime.combine(date.today(), datetime.min.time()),
        title=data.title,
        type=data.type,
        points=data.points,
        description=data.description,
        status=TaskStatus.pending,
        is_adhoc=True,
        is_conditional=False,
        created_by=user.id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    await log_action(db, user.id, "create_adhoc_task", "daily_task", task.id,
                     {"child_id": child_id, "title": data.title})
    return _task_to_response(task)
