import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.client.dependencies import resolve_target_client_id
from app.core.database import get_db
from app.shopping.schemas import ShoppingListPublic
from app.shopping.service import generate_shopping_list
from app.user.models import User

router = APIRouter(prefix="/shopping-list", tags=["shopping list"])


@router.get("/weekly", response_model=ShoppingListPublic)
async def handle_get_weekly_shopping_list(
    week_start: date,
    client_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if week_start.isoweekday() != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="week_start must be a Monday",
        )
    target_client_id = await resolve_target_client_id(db, user, client_id)
    return await generate_shopping_list(db, target_client_id, week_start)
