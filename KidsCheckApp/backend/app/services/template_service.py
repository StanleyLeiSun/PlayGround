from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import TaskTemplate, ConditionalTask, DailyTask, TaskStatus
from app.schemas.schemas import TaskTemplateCreate, TaskTemplateBatchCreate, TaskTemplateUpdate, ConditionalTaskCreate, ConditionalTaskUpdate

WEEKDAY_NAMES = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


async def get_templates(db: AsyncSession, child_id: int) -> list[dict]:
    result = await db.execute(
        select(TaskTemplate)
        .where(TaskTemplate.child_id == child_id)
        .order_by(TaskTemplate.weekday, TaskTemplate.sort_order)
    )
    templates = result.scalars().all()
    grouped: dict[int, list] = {}
    for t in templates:
        if t.weekday not in grouped:
            grouped[t.weekday] = []
        grouped[t.weekday].append(t)

    return [
        {
            "weekday": wd,
            "weekday_name": WEEKDAY_NAMES.get(wd, str(wd)),
            "templates": [
                {
                    "id": t.id, "child_id": t.child_id, "weekday": t.weekday,
                    "title": t.title, "type": t.type.value, "description": t.description,
                    "points": t.points, "sort_order": t.sort_order,
                }
                for t in tpls
            ],
        }
        for wd, tpls in sorted(grouped.items())
    ]


async def create_template(db: AsyncSession, child_id: int, data: TaskTemplateCreate) -> TaskTemplate:
    template = TaskTemplate(
        child_id=child_id,
        weekday=data.weekday,
        title=data.title,
        type=data.type,
        description=data.description,
        points=data.points,
        sort_order=data.sort_order,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


async def create_templates_batch(db: AsyncSession, child_id: int, data: TaskTemplateBatchCreate) -> list[TaskTemplate]:
    templates = []
    for weekday in data.weekdays:
        template = TaskTemplate(
            child_id=child_id,
            weekday=weekday,
            title=data.title,
            type=data.type,
            description=data.description,
            points=data.points,
            sort_order=data.sort_order,
        )
        db.add(template)
        templates.append(template)
    await db.flush()
    for t in templates:
        await db.refresh(t)
    return templates


async def update_template(db: AsyncSession, template_id: int, data: TaskTemplateUpdate) -> TaskTemplate | None:
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        return None
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(template, field, value)
    await db.flush()
    await db.refresh(template)

    today_start = datetime.combine(date.today(), datetime.min.time())
    sync_fields = {}
    if "points" in update_fields:
        sync_fields["points"] = update_fields["points"]
    if "title" in update_fields:
        sync_fields["title"] = update_fields["title"]
    if "description" in update_fields:
        sync_fields["description"] = update_fields["description"]
    if "type" in update_fields:
        sync_fields["type"] = update_fields["type"]
    if sync_fields:
        await db.execute(
            update(DailyTask)
            .where(
                DailyTask.source_template_id == template_id,
                DailyTask.date == today_start,
                DailyTask.status == TaskStatus.pending,
            )
            .values(**sync_fields)
        )

    return template


async def delete_template(db: AsyncSession, template_id: int) -> bool:
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        return False
    await db.delete(template)
    await db.flush()
    return True


async def get_conditional_tasks(db: AsyncSession, child_id: int) -> list[ConditionalTask]:
    result = await db.execute(
        select(ConditionalTask).where(ConditionalTask.child_id == child_id)
    )
    return list(result.scalars().all())


async def create_conditional_task(db: AsyncSession, child_id: int, data: ConditionalTaskCreate) -> ConditionalTask:
    task = ConditionalTask(
        child_id=child_id,
        title=data.title,
        type=data.type,
        description=data.description,
        points=data.points,
        weekdays=data.weekdays,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def update_conditional_task(db: AsyncSession, task_id: int, data: ConditionalTaskUpdate) -> ConditionalTask | None:
    result = await db.execute(select(ConditionalTask).where(ConditionalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.flush()
    await db.refresh(task)
    return task


async def delete_conditional_task(db: AsyncSession, task_id: int) -> bool:
    result = await db.execute(select(ConditionalTask).where(ConditionalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return False
    await db.delete(task)
    await db.flush()
    return True
