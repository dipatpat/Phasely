import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, oauth2_scheme
from app.auth.schemas import Token, UserPublic, UserRegister
from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.auth.service import EmailAlreadyExistsError, create_user, get_user_by_email
from app.core.database import get_db
from app.core.redis import get_redis
from app.user.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await get_user_by_email(db, data.email)
    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    hashed_password = hash_password(data.password)
    try:
        new_user = await create_user(
            db, data.first_name, data.last_name, data.email, hashed_password, data.role
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from e
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    username = form_data.username
    user = await get_user_by_email(db, username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, detail="Invalid email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def get_user(current_user: User = Depends(get_current_user)) -> UserPublic:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
    token: str = Depends(oauth2_scheme), redis: Redis = Depends(get_redis)
) -> None:
    expiration_time = decode_access_token(token).get("exp")
    remaining_time = expiration_time - int(time.time())
    await redis.set(f"blacklist:{token}", "0", ex=remaining_time)
