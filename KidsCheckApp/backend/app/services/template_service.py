from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import TaskTemplate, ConditionalTask
from app.schemas.schemas import TaskTemplateCreate, TaskTemplateUpdate, ConditionalTaskCreate

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


async def update_template(db: AsyncSession, template_id: int, data: TaskTemplateUpdate) -> TaskTemplate | None:
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await db.flush()
    await db.refresh(template)
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
    )
    db.add(task)
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
