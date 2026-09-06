from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import Token, UserPublic, UserRegister
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.database import get_db
from app.user.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == data.email, User.is_active.is_(True))
    )
    user_found = result.scalar_one_or_none()
    if user_found:
        raise HTTPException(409, detail="User with this email already exists")
    hashed_password = hash_password(data.password)
    new_user = User(
        email=data.email,
        hashed_password=hashed_password,
        role=data.role,
        is_active=True,
    )
    try:
        db.add(new_user)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(409, detail="Account with this email already exists") from e
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    username = form_data.username
    result = await db.execute(
        select(User).where(User.email == username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, detail="Invalid email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def get_user(current_user: User = Depends(get_current_user)) -> UserPublic:
    return current_user
