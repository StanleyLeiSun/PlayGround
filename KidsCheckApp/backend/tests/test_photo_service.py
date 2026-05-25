"""Tests for photo_service functions."""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DailyTask, TaskType, TaskStatus, CheckInPhoto
from app.services import photo_service


@pytest.fixture
async def sample_task(committed_db, seed_data):
    """Create a sample daily task for photo tests."""
    luobo = seed_data["luobo"]
    task = DailyTask(
        child_id=luobo.id,
        date=datetime(2026, 5, 22, 0, 0),
        title="Photo Task",
        type=TaskType.written,
        points=10,
        status=TaskStatus.pending,
    )
    committed_db.add(task)
    await committed_db.commit()
    return task


@pytest.mark.asyncio
async def test_save_photo(db: AsyncSession, seed_data, sample_task):
    """Test saving a photo."""
    luobo = seed_data["luobo"]
    task = sample_task

    # Create a small test image
    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    photo = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/jpeg"
    )
    assert photo.id is not None
    assert photo.daily_task_id == task.id
    assert photo.uploaded_by == luobo.id
    assert photo.photo_url.startswith("/photos/")
    assert photo.photo_url.endswith(".jpg")
    assert photo.reviewed is False
    assert photo.review_note is None


@pytest.mark.asyncio
async def test_save_photo_png(db: AsyncSession, seed_data, sample_task):
    """Test saving a PNG photo."""
    luobo = seed_data["luobo"]
    task = sample_task

    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    photo = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/png"
    )
    assert photo.photo_url.endswith(".png")


@pytest.mark.asyncio
async def test_save_photo_task_not_found(db: AsyncSession, seed_data):
    """Test saving a photo for non-existent task."""
    luobo = seed_data["luobo"]
    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with pytest.raises(ValueError, match="Task not found"):
        await photo_service.save_photo(
            db, 999, luobo.id, test_bytes, "image/jpeg"
        )


@pytest.mark.asyncio
async def test_get_photo(db: AsyncSession, seed_data, sample_task):
    """Test getting a photo by ID."""
    luobo = seed_data["luobo"]
    task = sample_task

    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    saved = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/jpeg"
    )

    photo = await photo_service.get_photo(db, saved.id)
    assert photo is not None
    assert photo.id == saved.id


@pytest.mark.asyncio
async def test_get_photo_not_found(db: AsyncSession):
    """Test getting a non-existent photo."""
    photo = await photo_service.get_photo(db, 999)
    assert photo is None


@pytest.mark.asyncio
async def test_review_photo(db: AsyncSession, seed_data, sample_task):
    """Test reviewing a photo."""
    luobo = seed_data["luobo"]
    task = sample_task

    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    saved = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/jpeg"
    )

    reviewed = await photo_service.review_photo(db, saved.id, True, "Good job!")
    assert reviewed is not None
    assert reviewed.reviewed is True
    assert reviewed.review_note == "Good job!"


@pytest.mark.asyncio
async def test_review_photo_reject(db: AsyncSession, seed_data, sample_task):
    """Test rejecting a photo."""
    luobo = seed_data["luobo"]
    task = sample_task

    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    saved = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/jpeg"
    )

    reviewed = await photo_service.review_photo(db, saved.id, False, "Try again")
    assert reviewed is not None
    assert reviewed.reviewed is False
    assert reviewed.review_note == "Try again"


@pytest.mark.asyncio
async def test_review_photo_not_found(db: AsyncSession):
    """Test reviewing a non-existent photo."""
    result = await photo_service.review_photo(db, 999, True, "Note")
    assert result is None


@pytest.mark.asyncio
async def test_review_photo_no_note(db: AsyncSession, seed_data, sample_task):
    """Test reviewing a photo without a note."""
    luobo = seed_data["luobo"]
    task = sample_task

    test_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    saved = await photo_service.save_photo(
        db, task.id, luobo.id, test_bytes, "image/jpeg"
    )

    reviewed = await photo_service.review_photo(db, saved.id, True, None)
    assert reviewed is not None
    assert reviewed.reviewed is True
    assert reviewed.review_note is None
