from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import User
from app.schemas.schemas import ConditionalTaskCreate, ConditionalTaskUpdate, ConditionalTaskResponse
from app.services import template_service
from app.services.action_log_service import log_action

router = APIRouter(prefix="/api/conditional-tasks", tags=["conditional-tasks"])


@router.get("/{child_id}", response_model=list[ConditionalTaskResponse])
async def get_conditional_tasks(
    child_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await template_service.get_conditional_tasks(db, child_id)
    return [
        ConditionalTaskResponse(
            id=t.id, child_id=t.child_id, trigger_condition=t.trigger_condition,
            title=t.title, type=t.type.value, description=t.description,
            points=t.points, weekdays=t.weekdays,
        )
        for t in tasks
    ]


@router.post("/{child_id}", response_model=ConditionalTaskResponse)
async def create_conditional_task(
    child_id: int,
    data: ConditionalTaskCreate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    task = await template_service.create_conditional_task(db, child_id, data)
    await log_action(db, user.id, "create_conditional_task", "conditional_task", task.id)
    return ConditionalTaskResponse(
        id=task.id, child_id=task.child_id, trigger_condition=task.trigger_condition,
        title=task.title, type=task.type.value, description=task.description,
        points=task.points, weekdays=task.weekdays,
    )


@router.put("/{task_id}", response_model=ConditionalTaskResponse)
async def update_conditional_task(
    task_id: int,
    data: ConditionalTaskUpdate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    task = await template_service.update_conditional_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Conditional task not found")
    await log_action(db, user.id, "update_conditional_task", "conditional_task", task_id)
    return ConditionalTaskResponse(
        id=task.id, child_id=task.child_id, trigger_condition=task.trigger_condition,
        title=task.title, type=task.type.value, description=task.description,
        points=task.points, weekdays=task.weekdays,
    )


@router.delete("/{task_id}")
async def delete_conditional_task(
    task_id: int,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    if not await template_service.delete_conditional_task(db, task_id):
        raise HTTPException(status_code=404, detail="Conditional task not found")
    await log_action(db, user.id, "delete_conditional_task", "conditional_task", task_id)
    return {"ok": True}
