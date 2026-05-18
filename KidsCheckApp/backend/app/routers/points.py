from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User
from app.schemas.schemas import PointBalanceResponse, PointTransactionResponse
from app.services import points_service

router = APIRouter(prefix="/api/points", tags=["points"])


@router.get("/{child_id}", response_model=PointBalanceResponse)
async def get_points(
    child_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    balance, transactions = await points_service.get_balance(db, child_id)
    return PointBalanceResponse(
        child_id=child_id,
        balance=balance,
        transactions=[
            PointTransactionResponse(
                id=t.id, child_id=t.child_id, amount=t.amount,
                reason=t.reason, related_task_id=t.related_task_id,
                created_at=t.created_at,
            )
            for t in transactions
        ],
    )
