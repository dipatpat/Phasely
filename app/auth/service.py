import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.user.models import User


class EmailAlreadyExistsError(Exception):
    pass


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, email: str, hashed_password: str, role: UserRole
) -> User:
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        is_active=True,
    )
    try:
        db.add(new_user)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise EmailAlreadyExistsError() from e
    await db.refresh(new_user)
    return new_user
