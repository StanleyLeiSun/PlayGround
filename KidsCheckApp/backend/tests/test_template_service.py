"""Tests for template_service functions."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import TaskTemplate, TaskType, ConditionalTask
from app.schemas.schemas import (
    TaskTemplateCreate, TaskTemplateBatchCreate, TaskTemplateUpdate,
    ConditionalTaskCreate, ConditionalTaskUpdate,
)
from app.services import template_service


@pytest.mark.asyncio
async def test_get_templates_empty(db: AsyncSession, seed_data):
    """Test getting templates when none exist."""
    luobo = seed_data["luobo"]
    result = await template_service.get_templates(db, luobo.id)
    assert result == []


@pytest.mark.asyncio
async def test_create_template(db: AsyncSession, seed_data):
    """Test creating a template."""
    luobo = seed_data["luobo"]
    data = TaskTemplateCreate(
        weekday=1,
        title="Reading Task",
        type=TaskType.reading,
        description="Read a book",
        points=10,
        sort_order=1,
    )
    template = await template_service.create_template(db, luobo.id, data)
    assert template.id is not None
    assert template.child_id == luobo.id
    assert template.weekday == 1
    assert template.title == "Reading Task"


@pytest.mark.asyncio
async def test_get_templates_after_create(db: AsyncSession, seed_data):
    """Test getting templates after creating some."""
    luobo = seed_data["luobo"]
    data1 = TaskTemplateCreate(
        weekday=1, title="Task 1", type=TaskType.reading,
        description=None, points=10, sort_order=1,
    )
    data2 = TaskTemplateCreate(
        weekday=1, title="Task 2", type=TaskType.written,
        description=None, points=15, sort_order=2,
    )
    data3 = TaskTemplateCreate(
        weekday=2, title="Task 3", type=TaskType.reading,
        description=None, points=10, sort_order=1,
    )
    await template_service.create_template(db, luobo.id, data1)
    await template_service.create_template(db, luobo.id, data2)
    await template_service.create_template(db, luobo.id, data3)

    result = await template_service.get_templates(db, luobo.id)
    assert len(result) == 2  # 2 weekdays
    assert result[0]["weekday"] == 1
    assert len(result[0]["templates"]) == 2
    assert result[1]["weekday"] == 2
    assert len(result[1]["templates"]) == 1


@pytest.mark.asyncio
async def test_create_templates_batch(db: AsyncSession, seed_data):
    """Test batch creating templates."""
    luobo = seed_data["luobo"]
    data = TaskTemplateBatchCreate(
        weekdays=[1, 2, 3],
        title="Daily Task",
        type=TaskType.reading,
        description=None,
        points=10,
        sort_order=1,
    )
    templates = await template_service.create_templates_batch(db, luobo.id, data)
    assert len(templates) == 3
    for t in templates:
        assert t.title == "Daily Task"
        assert t.child_id == luobo.id


@pytest.mark.asyncio
async def test_update_template(db: AsyncSession, seed_data):
    """Test updating a template."""
    luobo = seed_data["luobo"]
    data = TaskTemplateCreate(
        weekday=1, title="Old Title", type=TaskType.reading,
        description=None, points=10, sort_order=1,
    )
    template = await template_service.create_template(db, luobo.id, data)

    update_data = TaskTemplateUpdate(title="New Title", points=20)
    updated = await template_service.update_template(db, template.id, update_data)
    assert updated is not None
    assert updated.title == "New Title"
    assert updated.points == 20


@pytest.mark.asyncio
async def test_update_template_not_found(db: AsyncSession):
    """Test updating a non-existent template."""
    update_data = TaskTemplateUpdate(title="New Title")
    result = await template_service.update_template(db, 999, update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_template(db: AsyncSession, seed_data):
    """Test deleting a template."""
    luobo = seed_data["luobo"]
    data = TaskTemplateCreate(
        weekday=1, title="To Delete", type=TaskType.reading,
        description=None, points=10, sort_order=1,
    )
    template = await template_service.create_template(db, luobo.id, data)

    result = await template_service.delete_template(db, template.id)
    assert result is True

    templates = await template_service.get_templates(db, luobo.id)
    assert len(templates) == 0


@pytest.mark.asyncio
async def test_delete_template_not_found(db: AsyncSession):
    """Test deleting a non-existent template."""
    result = await template_service.delete_template(db, 999)
    assert result is False


@pytest.mark.asyncio
async def test_get_conditional_tasks_empty(db: AsyncSession, seed_data):
    """Test getting conditional tasks when none exist."""
    luobo = seed_data["luobo"]
    result = await template_service.get_conditional_tasks(db, luobo.id)
    assert result == []


@pytest.mark.asyncio
async def test_create_conditional_task(db: AsyncSession, seed_data):
    """Test creating a conditional task."""
    luobo = seed_data["luobo"]
    data = ConditionalTaskCreate(
        title="Bonus Task",
        type=TaskType.reading,
        description="Extra reading",
        points=15,
        weekdays="1,2,3",
    )
    task = await template_service.create_conditional_task(db, luobo.id, data)
    assert task.id is not None
    assert task.child_id == luobo.id
    assert task.title == "Bonus Task"


@pytest.mark.asyncio
async def test_update_conditional_task(db: AsyncSession, seed_data):
    """Test updating a conditional task."""
    luobo = seed_data["luobo"]
    data = ConditionalTaskCreate(
        title="Old Title", type=TaskType.reading,
        description=None, points=10, weekdays=None,
    )
    task = await template_service.create_conditional_task(db, luobo.id, data)

    update_data = ConditionalTaskUpdate(title="New Title", points=20)
    updated = await template_service.update_conditional_task(db, task.id, update_data)
    assert updated is not None
    assert updated.title == "New Title"
    assert updated.points == 20


@pytest.mark.asyncio
async def test_update_conditional_task_not_found(db: AsyncSession):
    """Test updating a non-existent conditional task."""
    update_data = ConditionalTaskUpdate(title="New Title")
    result = await template_service.update_conditional_task(db, 999, update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_conditional_task(db: AsyncSession, seed_data):
    """Test deleting a conditional task."""
    luobo = seed_data["luobo"]
    data = ConditionalTaskCreate(
        title="To Delete", type=TaskType.reading,
        description=None, points=10, weekdays=None,
    )
    task = await template_service.create_conditional_task(db, luobo.id, data)

    result = await template_service.delete_conditional_task(db, task.id)
    assert result is True

    tasks = await template_service.get_conditional_tasks(db, luobo.id)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_delete_conditional_task_not_found(db: AsyncSession):
    """Test deleting a non-existent conditional task."""
    result = await template_service.delete_conditional_task(db, 999)
    assert result is False


@pytest.mark.asyncio
async def test_get_templates_weekday_names(db: AsyncSession, seed_data):
    """Test that weekday names are returned correctly."""
    luobo = seed_data["luobo"]
    data = TaskTemplateCreate(
        weekday=1, title="Monday Task", type=TaskType.reading,
        description=None, points=10, sort_order=1,
    )
    await template_service.create_template(db, luobo.id, data)

    result = await template_service.get_templates(db, luobo.id)
    assert result[0]["weekday_name"] == "周一"


@pytest.mark.asyncio
async def test_get_templates_sorted_by_weekday(db: AsyncSession, seed_data):
    """Test that templates are sorted by weekday."""
    luobo = seed_data["luobo"]
    # Create in reverse order
    for wd in [3, 1, 2]:
        data = TaskTemplateCreate(
            weekday=wd, title=f"Task {wd}", type=TaskType.reading,
            description=None, points=10, sort_order=1,
        )
        await template_service.create_template(db, luobo.id, data)

    result = await template_service.get_templates(db, luobo.id)
    weekdays = [r["weekday"] for r in result]
    assert weekdays == [1, 2, 3]
