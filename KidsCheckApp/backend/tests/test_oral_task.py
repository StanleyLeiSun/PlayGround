"""Tests for oral (英语口语练习) task type."""
import pytest
import pytest_asyncio
from datetime import date

from tests.conftest import auth_header


# ── Helpers ───────────────────────────────────────────────────────────────────

async def create_oral_template(client, parent_token, child_id, title="英语口语：Animals", points=10):
    """Create an oral task template via API."""
    weekday = date.today().isoweekday()
    resp = await client.post(
        f"/api/templates/{child_id}",
        headers=auth_header(parent_token),
        json={
            "weekday": weekday,
            "title": title,
            "type": "oral",
            "description": "看图说出动物的英文名称",
            "points": points,
        },
    )
    assert resp.status_code == 200
    return resp.json()


async def create_written_template(client, parent_token, child_id):
    """Create a written task template via API."""
    weekday = date.today().isoweekday()
    resp = await client.post(
        f"/api/templates/{child_id}",
        headers=auth_header(parent_token),
        json={"weekday": weekday, "title": "数学练习", "type": "written", "points": 5},
    )
    assert resp.status_code == 200
    return resp.json()


async def upload_oral_image(client, parent_token, template_id, image_bytes=b"\x89PNG" + b"\x00" * 100):
    """Upload image to an oral template."""
    resp = await client.put(
        f"/api/templates/{template_id}/oral-image",
        headers=auth_header(parent_token),
        files={"image": ("test.jpg", image_bytes, "image/jpeg")},
    )
    return resp


async def get_oral_task(client, parent_token, child_id):
    """Get the first oral task for today."""
    today = date.today().isoformat()
    resp = await client.get(
        f"/api/daily-tasks/{child_id}/{today}",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    oral_tasks = [t for t in resp.json() if t["type"] == "oral"]
    assert len(oral_tasks) >= 1, f"No oral tasks found in {resp.json()}"
    return oral_tasks[0]


async def upload_recording(client, token, task_id, duration=45.0, audio_bytes=None):
    """Upload a recording to a task."""
    if audio_bytes is None:
        audio_bytes = b"\x00" * 1024
    return await client.post(
        f"/api/daily-tasks/{task_id}/recording",
        headers=auth_header(token),
        files={"audio": ("recording.m4a", audio_bytes, "audio/mp4")},
        data={"duration": str(duration)},
    )


# ── Template Image Upload ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_oral_image(client, parent_token, seed_data):
    """Uploading image to oral template succeeds."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)

    resp = await upload_oral_image(client, parent_token, tmpl["id"])
    assert resp.status_code == 200
    assert resp.json()["oral_image_url"].startswith("/photos/oral/")


@pytest.mark.asyncio
async def test_upload_oral_image_non_oral_template(client, parent_token, seed_data):
    """Uploading image to non-oral template returns 400."""
    child_id = seed_data["luobo"].id
    tmpl = await create_written_template(client, parent_token, child_id)

    resp = await upload_oral_image(client, parent_token, tmpl["id"])
    assert resp.status_code == 400
    assert "oral templates" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oral_image_too_large(client, parent_token, seed_data):
    """Uploading oversized image returns 400."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)

    large_bytes = b"\x89PNG" + b"\x00" * 6_000_000
    resp = await upload_oral_image(client, parent_token, tmpl["id"], large_bytes)
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oral_image_nonexistent_template(client, parent_token):
    """Uploading to non-existent template returns 404."""
    resp = await upload_oral_image(client, parent_token, 9999)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_oral_image_grandparent_forbidden(client, grandparent_token, seed_data, parent_token):
    """Grandparents cannot upload template images."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)

    resp = await upload_oral_image(client, grandparent_token, tmpl["id"])
    assert resp.status_code == 403


# ── Task Generation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_oral_task_snapshots_image(client, parent_token, seed_data):
    """Generated daily task has oral_image_url snapshot from template."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)

    # Upload image to template
    await upload_oral_image(client, parent_token, tmpl["id"])

    # Fetch daily tasks triggers generation
    oral_task = await get_oral_task(client, parent_token, child_id)
    assert oral_task["oral_image_url"].startswith("/photos/oral/")


@pytest.mark.asyncio
async def test_generate_oral_task_without_image(client, parent_token, seed_data):
    """Generated daily task has null oral_image_url when template has no image."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id, title="英语口语：Colors", points=5)

    oral_task = await get_oral_task(client, parent_token, child_id)
    assert oral_task["oral_image_url"] is None


@pytest.mark.asyncio
async def test_update_image_does_not_affect_existing_tasks(client, parent_token, seed_data):
    """Updating template image doesn't change already-generated daily tasks."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)

    # Generate tasks (triggers snapshot)
    oral_task = await get_oral_task(client, parent_token, child_id)
    old_image = oral_task["oral_image_url"]  # None since no image yet

    # Upload image to template
    await upload_oral_image(client, parent_token, tmpl["id"])

    # Re-fetch - old task should still have null image
    oral_task2 = await get_oral_task(client, parent_token, child_id)
    assert oral_task2["oral_image_url"] == old_image


# ── Recording Upload & Task Completion ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_recording_completes_task(client, parent_token, seed_data):
    """Uploading recording auto-completes the task and awards points."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id, points=10)
    oral_task = await get_oral_task(client, parent_token, child_id)
    assert oral_task["status"] == "pending"

    resp = await upload_recording(client, parent_token, oral_task["id"], duration=45.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"]["status"] == "done"
    assert data["recording"]["audio_url"].startswith("/recordings/")
    assert data["recording"]["duration"] == 45.0

    # Check points
    resp_points = await client.get(
        f"/api/points/{child_id}",
        headers=auth_header(parent_token),
    )
    assert resp_points.json()["balance"] == 10


@pytest.mark.asyncio
async def test_upload_recording_too_short(client, parent_token, seed_data):
    """Recording shorter than 30 seconds is rejected."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)

    resp = await upload_recording(client, parent_token, oral_task["id"], duration=20.0)
    assert resp.status_code == 400
    assert "30 seconds" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_recording_to_non_oral_task(client, parent_token, seed_data):
    """Uploading recording to non-oral task returns 400."""
    child_id = seed_data["luobo"].id
    await create_written_template(client, parent_token, child_id)

    today = date.today().isoformat()
    resp = await client.get(
        f"/api/daily-tasks/{child_id}/{today}",
        headers=auth_header(parent_token),
    )
    written_task = [t for t in resp.json() if t["type"] == "written"][0]

    resp = await upload_recording(client, parent_token, written_task["id"], duration=45.0)
    assert resp.status_code == 400
    assert "oral" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_recording_to_already_completed_task(client, parent_token, seed_data):
    """Uploading recording to already completed task returns 400."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)

    # First upload
    await upload_recording(client, parent_token, oral_task["id"], duration=45.0)

    # Second upload should fail
    resp = await upload_recording(client, parent_token, oral_task["id"], duration=50.0)
    assert resp.status_code == 400
    assert "Already completed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_recording_triggers_conditional_tasks(
    client, parent_token, seed_data, committed_db
):
    """Recording upload triggers conditional task insertion when all required tasks done."""
    child_id = seed_data["luobo"].id

    # Create a conditional task
    from app.models.models import ConditionalTask, TaskType
    ct = ConditionalTask(
        child_id=child_id,
        trigger_condition="all_required_done",
        title="额外奖励任务",
        type=TaskType.reading,
        points=20,
    )
    committed_db.add(ct)
    await committed_db.flush()
    await committed_db.commit()

    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)

    # Complete the oral task
    await upload_recording(client, parent_token, oral_task["id"], duration=60.0)

    # Check conditional task was inserted
    today = date.today().isoformat()
    resp = await client.get(
        f"/api/daily-tasks/{child_id}/{today}",
        headers=auth_header(parent_token),
    )
    cond_tasks = [t for t in resp.json() if t["is_conditional"]]
    assert len(cond_tasks) >= 1
    assert cond_tasks[0]["title"] == "额外奖励任务"


# ── Get Recordings ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_recordings(client, parent_token, seed_data):
    """Get recordings returns list ordered by recorded_at desc."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)

    await upload_recording(client, parent_token, oral_task["id"], duration=45.0)

    resp = await client.get(
        f"/api/daily-tasks/{oral_task['id']}/recordings",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    recordings = resp.json()
    assert len(recordings) == 1
    assert recordings[0]["duration"] == 45.0


@pytest.mark.asyncio
async def test_get_recordings_empty(client, parent_token, seed_data):
    """Get recordings for task with no recordings returns empty list."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)

    resp = await client.get(
        f"/api/daily-tasks/{oral_task['id']}/recordings",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ── Undo Preserves Recordings ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_undo_oral_task_preserves_recording(client, parent_token, seed_data):
    """Undoing an oral task preserves the recording."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id, points=10)
    oral_task = await get_oral_task(client, parent_token, child_id)

    # Upload recording (completes task)
    await upload_recording(client, parent_token, oral_task["id"], duration=45.0)

    # Undo
    resp = await client.post(
        f"/api/daily-tasks/{oral_task['id']}/undo",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # Recording should still exist
    resp = await client.get(
        f"/api/daily-tasks/{oral_task['id']}/recordings",
        headers=auth_header(parent_token),
    )
    assert len(resp.json()) == 1

    # Points should be reverted
    resp_points = await client.get(
        f"/api/points/{child_id}",
        headers=auth_header(parent_token),
    )
    assert resp_points.json()["balance"] == 0


# ── Oral Recording Response in Task List ──────────────────────────────────────

@pytest.mark.asyncio
async def test_task_list_includes_recordings(client, parent_token, seed_data):
    """Daily task list response includes recordings for oral tasks."""
    child_id = seed_data["luobo"].id
    await create_oral_template(client, parent_token, child_id)
    oral_task = await get_oral_task(client, parent_token, child_id)
    assert "recordings" in oral_task
    assert oral_task["recordings"] == []

    await upload_recording(client, parent_token, oral_task["id"], duration=45.0)

    oral_task2 = await get_oral_task(client, parent_token, child_id)
    assert len(oral_task2["recordings"]) == 1
    assert oral_task2["recordings"][0]["duration"] == 45.0


# ── Template Response Includes oral_image_url ─────────────────────────────────

@pytest.mark.asyncio
async def test_template_response_includes_oral_image_url(client, parent_token, seed_data):
    """Template list response includes oral_image_url for oral templates."""
    child_id = seed_data["luobo"].id
    tmpl = await create_oral_template(client, parent_token, child_id)
    await upload_oral_image(client, parent_token, tmpl["id"])

    resp = await client.get(
        f"/api/templates/{child_id}",
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    all_templates = [
        t for templates_by_day in resp.json()
        for t in templates_by_day["templates"]
    ]
    oral_tmpl = [t for t in all_templates if t["type"] == "oral"]
    assert len(oral_tmpl) >= 1
    assert oral_tmpl[0]["oral_image_url"].startswith("/photos/oral/")
