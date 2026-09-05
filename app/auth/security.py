from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class AuthError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code


class TokenExpiredError(AuthError):
    def __init__(self):
        super().__init__("Token has expired", 401)


class TokenInvalidError(AuthError):
    def __init__(self):
        super().__init__("Token is invalid", 401)


def hash_password(password: str) -> str:
    return PasswordHash.recommended().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PasswordHash.recommended().verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError() from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError() from e
