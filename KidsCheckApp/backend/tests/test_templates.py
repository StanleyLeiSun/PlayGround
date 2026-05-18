"""Tests for task template CRUD, conditional tasks, and voice parsing."""
import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_create_written_template(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "数学口算", "type": "written", "description": "2页", "points": 5},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "数学口算"
    assert data["type"] == "written"
    assert data["points"] == 5
    assert data["child_id"] == child_id


@pytest.mark.asyncio
async def test_create_reading_template(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 2, "title": "英语阅读", "type": "reading", "points": 3},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "reading"


@pytest.mark.asyncio
async def test_list_templates_grouped_by_weekday(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    # Create templates for different weekdays
    await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "任务A", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )
    await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "任务B", "type": "reading", "points": 3},
        headers=auth_header(parent_token),
    )
    await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 3, "title": "任务C", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )

    resp = await client.get(f"/api/templates/{child_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200
    groups = resp.json()
    assert len(groups) == 2  # weekday 1 and 3
    monday = next(g for g in groups if g["weekday"] == 1)
    assert len(monday["templates"]) == 2


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    create_resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "旧标题", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )
    template_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/templates/{template_id}",
        json={"title": "新标题", "points": 10},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"
    assert resp.json()["points"] == 10


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    create_resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "待删除", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )
    template_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/templates/{template_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200

    # Verify deleted
    list_resp = await client.get(f"/api/templates/{child_id}", headers=auth_header(parent_token))
    all_templates = [t for g in list_resp.json() for t in g["templates"]]
    assert all(t["id"] != template_id for t in all_templates)


@pytest.mark.asyncio
async def test_delete_nonexistent_template(client: AsyncClient, parent_token):
    resp = await client.delete("/api/templates/99999", headers=auth_header(parent_token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_conditional_task(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    resp = await client.post(
        f"/api/conditional-tasks/{child_id}",
        json={"title": "画画", "type": "written", "description": "30分钟", "points": 5},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "画画"
    assert data["trigger_condition"] == "all_required_done"


@pytest.mark.asyncio
async def test_list_conditional_tasks(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    await client.post(
        f"/api/conditional-tasks/{child_id}",
        json={"title": "画画", "type": "written", "points": 5},
        headers=auth_header(parent_token),
    )
    resp = await client.get(f"/api/conditional-tasks/{child_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_conditional_task(client: AsyncClient, parent_token, seed_data):
    child_id = seed_data["luobo"].id
    create_resp = await client.post(
        f"/api/conditional-tasks/{child_id}",
        json={"title": "待删除条件", "type": "reading", "points": 3},
        headers=auth_header(parent_token),
    )
    task_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/conditional-tasks/{task_id}", headers=auth_header(parent_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_voice_create_intent(client: AsyncClient, parent_token, seed_data):
    import json
    body = json.dumps({"text": "每周一给萝卜添加数学口算，5积分"}).encode("utf-8")
    resp = await client.post(
        "/api/templates/voice",
        content=body,
        headers={**auth_header(parent_token), "Content-Type": "application/json; charset=utf-8"},
    )
    if resp.status_code == 422:
        # Print validation error for debugging
        print(f"422 error: {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "create"


@pytest.mark.asyncio
async def test_grandparent_cannot_create_template(client: AsyncClient, grandparent_token, seed_data):
    child_id = seed_data["luobo"].id
    resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "test", "type": "written", "points": 5},
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_grandparent_can_list_templates(client: AsyncClient, grandparent_token, seed_data):
    child_id = seed_data["luobo"].id
    resp = await client.get(f"/api/templates/{child_id}", headers=auth_header(grandparent_token))
    assert resp.status_code == 200
