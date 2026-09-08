import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str | None = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    first_name: str
    last_name: str
    email: str
    role: UserRole
    id: uuid.UUID
    is_active: bool


class UserRegister(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole


class UserLogin(BaseModel):
    email: str
    password: str
