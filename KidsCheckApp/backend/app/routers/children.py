from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import Child, User
from app.schemas.schemas import ChildResponse

router = APIRouter(prefix="/api/children", tags=["children"])


@router.get("", response_model=list[ChildResponse])
async def list_children(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Child).order_by(Child.id))
    children = result.scalars().all()
    return [ChildResponse(id=c.id, name=c.name, nickname=c.nickname, age=c.age) for c in children]
