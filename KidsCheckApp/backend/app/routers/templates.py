from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_parent
from app.models.models import User
from app.schemas.schemas import (
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateResponse,
    ConditionalTaskCreate, ConditionalTaskResponse, VoiceRequest, VoiceParsedIntent,
)
from app.services import template_service
from app.services.voice_service import parse_intent
from app.services.action_log_service import log_action

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/{child_id}")
async def get_templates(
    child_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await template_service.get_templates(db, child_id)


@router.post("/{child_id}", response_model=TaskTemplateResponse)
async def create_template(
    child_id: int,
    data: TaskTemplateCreate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    template = await template_service.create_template(db, child_id, data)
    await log_action(db, user.id, "create_template", "task_template", template.id,
                     {"child_id": child_id, "weekday": data.weekday, "title": data.title})
    return TaskTemplateResponse(
        id=template.id, child_id=template.child_id, weekday=template.weekday,
        title=template.title, type=template.type.value,
        description=template.description, points=template.points, sort_order=template.sort_order,
    )


@router.put("/{template_id}", response_model=TaskTemplateResponse)
async def update_template(
    template_id: int,
    data: TaskTemplateUpdate,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    template = await template_service.update_template(db, template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await log_action(db, user.id, "update_template", "task_template", template_id)
    return TaskTemplateResponse(
        id=template.id, child_id=template.child_id, weekday=template.weekday,
        title=template.title, type=template.type.value,
        description=template.description, points=template.points, sort_order=template.sort_order,
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    if not await template_service.delete_template(db, template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    await log_action(db, user.id, "delete_template", "task_template", template_id)
    return {"ok": True}


@router.post("/voice", response_model=VoiceParsedIntent)
async def voice_input(
    req: VoiceRequest,
    user: User = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await parse_intent(req.text)
    await log_action(db, user.id, "voice_input", metadata={"text": req.text, "parsed": result})
    return VoiceParsedIntent(**result)
